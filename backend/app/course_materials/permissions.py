"""Authorization and tenant boundary enforcement for Course Materials."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as database
from app.core.models import Role, SchoolClass, Student, Subject, Teacher, User
from app.core.school_access import resolve_staff_access
from app.course_materials import crud
from app.integrations.search_sphere.identifiers import build_collection_id
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

logger = logging.getLogger("exam_arena.course_materials.permissions")


async def resolve_teacher_school_affiliation(
    current_user: UserResponse,
    session: AsyncSession | None = None,
) -> tuple[str, Teacher | None]:
    """
    Resolve and verify authenticated teacher/principal's affiliated school ID.
    Raises 403 if the user is not a teacher/principal or not affiliated with a school.
    """
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers, principals, or administrators can manage course materials.",
        )

    if session is None:
        async with database.get_session() as db:
            return await resolve_teacher_school_affiliation(current_user, db)
    access = await resolve_staff_access(current_user, session)
    teacher = await get_teacher_by_user_id(current_user.id, session=session)
    return access.school_id, teacher


async def require_school_class(
    school_id: str, class_id: str | None, session: AsyncSession
) -> None:
    if not class_id:
        return
    found = await session.scalar(
        select(SchoolClass.id).where(
            SchoolClass.id == class_id, SchoolClass.schoolId == school_id
        )
    )
    if found is None:
        raise HTTPException(status_code=404, detail="Class not found in this school.")


async def resolve_user_material_scope(
    current_user: UserResponse,
    requested_class_id: str | None,
    session: AsyncSession,
) -> tuple[str, tuple[str, ...] | None]:
    """Return school and allowed classes; shared school resources remain visible."""
    if current_user.role in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
        access = await resolve_staff_access(current_user, session)
        await require_school_class(access.school_id, requested_class_id, session)
        if requested_class_id and not access.permits(
            access.school_id, requested_class_id
        ):
            raise HTTPException(
                403, "Course material access requires an assigned class."
            )
        return access.school_id, access.class_ids

    if current_user.role == Role.STUDENT:
        stmt = (
            select(Student)
            .where(Student.userId == current_user.id)
            .execution_options(populate_existing=True)
        )
        res = await session.execute(stmt)
        student = res.scalar_one_or_none()
        if not student or not student.schoolId or not student.classId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student is not enrolled in an active school.",
            )

        if requested_class_id and requested_class_id != student.classId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only search course materials for their enrolled class.",
            )

        await require_school_class(student.schoolId, student.classId, session)
        return student.schoolId, (student.classId,)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unauthorized role for searching course materials.",
    )


async def resolve_user_search_school_id(
    current_user: UserResponse,
    requested_class_id: str | None,
    session: AsyncSession,
) -> str:
    school_id, _ = await resolve_user_material_scope(
        current_user, requested_class_id, session
    )
    return school_id


async def assert_material_response_access(
    current_user: UserResponse,
    expected_school_id: str,
    requested_class_id: str | None,
    session: AsyncSession,
) -> None:
    """Re-read caller grants after upstream work, bypassing ORM identity caches."""
    role = await session.scalar(select(User.role).where(User.id == current_user.id))
    if role == current_user.role:
        school_id, _ = await resolve_user_material_scope(
            current_user, requested_class_id, session
        )
        if school_id == expected_school_id:
            return
    raise HTTPException(403, "Course material access changed.")


async def resolve_cleanup_scope(
    current_user: UserResponse,
    school_id: str,
    material_id: str,
    subject: Subject | None,
    class_id: str | None,
    session: AsyncSession,
) -> tuple[str | None, str | None]:
    """Use current catalog authority when available, otherwise require bound scope."""
    if subject is None and (current_user.role == Role.TEACHER or class_id is not None):
        _, visible_classes = await resolve_user_material_scope(
            current_user, None, session
        )
        material = await crud.get_course_material_by_id(
            session, material_id, school_id=school_id, visible_class_ids=visible_classes
        )
        if material is None:
            raise HTTPException(
                422,
                "Cleanup verification requires the document subject and class scope.",
            )
        if class_id is not None and class_id != material.classId:
            raise HTTPException(403, "Cleanup scope conflicts with the document.")
        subject, class_id = material.subject, material.classId
    await resolve_user_material_scope(current_user, class_id, session)
    collection_id = (
        build_collection_id(subject=subject, class_id=class_id)
        if subject is not None
        else None
    )
    return collection_id, class_id
