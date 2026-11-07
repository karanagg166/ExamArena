"""Authorization and tenant boundary enforcement for Course Materials."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role, SchoolClass, Student, Teacher
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

logger = logging.getLogger("exam_arena.course_materials.permissions")


async def resolve_teacher_school_affiliation(
    current_user: UserResponse,
    session: AsyncSession | None = None,
) -> tuple[str, Teacher]:
    """
    Resolve and verify authenticated teacher/principal's affiliated school ID.
    Raises 403 if the user is not a teacher/principal or not affiliated with a school.
    """
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers, principals, or administrators can manage course materials.",
        )

    teacher = await get_teacher_by_user_id(current_user.id, session=session)
    if not teacher or not teacher.schoolId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not affiliated with any active school.",
        )

    return teacher.schoolId, teacher


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
) -> tuple[str, str | None]:
    """
    Return the current school and optional enrolled-class read restriction.
    Enforces that:
    - Teachers search within their own school.
    - Students search strictly within their enrolled school (and optionally enrolled class).
    - Prevents cross-tenant queries.
    """
    if current_user.role in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
        teacher = await get_teacher_by_user_id(current_user.id, session=session)
        if not teacher or not teacher.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not affiliated with any active school.",
            )
        await require_school_class(teacher.schoolId, requested_class_id, session)
        return teacher.schoolId, None

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
        return student.schoolId, student.classId

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
