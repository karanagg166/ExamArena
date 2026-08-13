from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import Principal, School, Student, Teacher, User
from app.school.schemas import (
    SchoolCreateRequest,
    SchoolFilterParams,
    SchoolResponse,
    SchoolUpdateRequest,
)

SCHOOL_OPTIONS = [
    selectinload(School.principals)
    .selectinload(Principal.teacher)
    .selectinload(Teacher.user)
]


def _extract_principal_name(school: Any) -> str | None:
    principals = getattr(school, "principals", None) or []
    for principal in principals:
        teacher = getattr(principal, "teacher", None)
        user = getattr(teacher, "user", None)
        name = getattr(user, "name", None)
        if name:
            return cast(str, name)
    return None


def _to_school_response(school: Any) -> SchoolResponse:
    response = SchoolResponse.model_validate(school)
    principal_name = _extract_principal_name(school)
    if principal_name:
        return response.model_copy(update={"principalName": principal_name})
    return response


async def create_school(
    school_data: SchoolCreateRequest, user_id: str, session: AsyncSession | None = None
) -> SchoolResponse:
    """Create a school owned by the authenticated user."""
    data_dict = school_data.model_dump(exclude_none=True)
    data_dict["createdBy"] = user_id

    async def _do_create(s: AsyncSession):
        school = School(**data_dict)
        s.add(school)
        await s.commit()

        # Re-query with eager loading
        stmt = select(School).where(School.id == school.id).options(*SCHOOL_OPTIONS)
        res = await s.execute(stmt)
        created_school = res.scalar_one()
        return _to_school_response(created_school)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_school_by_user_id(
    user_id: str, session: AsyncSession | None = None
) -> SchoolResponse | None:
    """Get a school by creator user ID."""

    async def _do_get(s: AsyncSession):
        user_stmt = select(User).where(User.id == user_id)
        user = (await s.execute(user_stmt)).scalar_one_or_none()
        if not user:
            return None

        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)

        if role_value == "PRINCIPAL":
            teacher_stmt = select(Teacher).where(Teacher.userId == user_id)
            teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
            if not teacher:
                return None

            princ_stmt = select(Principal).where(Principal.teacherId == teacher.id)
            principal = (await s.execute(princ_stmt)).scalar_one_or_none()
            school_id = (
                principal.schoolId
                if principal and getattr(principal, "schoolId", None)
                else teacher.schoolId
            )
            if not school_id:
                return None

            school_stmt = (
                select(School).where(School.id == school_id).options(*SCHOOL_OPTIONS)
            )
            school = (await s.execute(school_stmt)).scalar_one_or_none()
            return _to_school_response(school) if school else None

        if role_value == "TEACHER":
            teacher_stmt = select(Teacher).where(Teacher.userId == user_id)
            teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
            if not teacher or not teacher.schoolId:
                return None
            school_stmt = (
                select(School)
                .where(School.id == teacher.schoolId)
                .options(*SCHOOL_OPTIONS)
            )
            school = (await s.execute(school_stmt)).scalar_one_or_none()
            return _to_school_response(school) if school else None

        if role_value == "STUDENT":
            student_stmt = select(Student).where(Student.userId == user_id)
            student = (await s.execute(student_stmt)).scalar_one_or_none()
            if not student:
                return None

            school_stmt = (
                select(School)
                .where(School.id == student.schoolId)
                .options(*SCHOOL_OPTIONS)
            )
            school = (await s.execute(school_stmt)).scalar_one_or_none()
            return _to_school_response(school) if school else None

        school_stmt = (
            select(School).where(School.createdBy == user_id).options(*SCHOOL_OPTIONS)
        )
        school = (await s.execute(school_stmt)).scalars().first()
        return _to_school_response(school) if school else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def update_school(
    school_id: str,
    school_data: SchoolUpdateRequest,
    session: AsyncSession | None = None,
) -> SchoolResponse | None:
    """Update a school by ID."""
    update_dict = school_data.model_dump(exclude_unset=True)

    async def _do_update(s: AsyncSession):
        stmt = select(School).where(School.id == school_id).options(*SCHOOL_OPTIONS)
        school = (await s.execute(stmt)).scalar_one_or_none()
        if not school:
            return None

        if update_dict:
            for k, v in update_dict.items():
                setattr(school, k, v)
            await s.commit()
            await s.refresh(school)
            res = await s.execute(
                select(School).where(School.id == school_id).options(*SCHOOL_OPTIONS)
            )
            school = res.scalar_one()

        return _to_school_response(school)

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_school(
    school_id: str, session: AsyncSession | None = None
) -> SchoolResponse | None:
    """Delete a school by ID."""

    async def _do_delete(s: AsyncSession):
        stmt = select(School).where(School.id == school_id).options(*SCHOOL_OPTIONS)
        school = (await s.execute(stmt)).scalar_one_or_none()
        if not school:
            return None
        response = _to_school_response(school)
        await s.delete(school)
        await s.commit()
        return response

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)


async def get_school_by_id(
    school_id: str, session: AsyncSession | None = None
) -> SchoolResponse | None:
    """Get a school by its database ID."""

    async def _do_get(s: AsyncSession):
        stmt = select(School).where(School.id == school_id).options(*SCHOOL_OPTIONS)
        school = (await s.execute(stmt)).scalar_one_or_none()
        return _to_school_response(school) if school else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_schools(
    filters: SchoolFilterParams, session: AsyncSession | None = None
) -> list[SchoolResponse]:
    """Get all schools with optional filters."""

    async def _do_get_all(s: AsyncSession):
        stmt = select(School).options(*SCHOOL_OPTIONS)

        if filters.name:
            stmt = stmt.where(School.name.ilike(f"%{filters.name}%"))
        if filters.city:
            stmt = stmt.where(School.city.ilike(f"%{filters.city}%"))
        if filters.state:
            stmt = stmt.where(School.state.ilike(f"%{filters.state}%"))
        if filters.country:
            stmt = stmt.where(School.country.ilike(f"%{filters.country}%"))
        if filters.pincode:
            stmt = stmt.where(School.pincode.ilike(f"%{filters.pincode}%"))
        if filters.school_code:
            stmt = stmt.where(School.schoolCode.ilike(f"%{filters.school_code}%"))
        if filters.email:
            stmt = stmt.where(School.email.ilike(f"%{filters.email}%"))
        if filters.website:
            stmt = stmt.where(School.website.ilike(f"%{filters.website}%"))
        if filters.school_type:
            stmt = stmt.where(School.type == filters.school_type)

        schools = (await s.execute(stmt)).scalars().all()
        return [_to_school_response(school) for school in schools]

    if session:
        return await _do_get_all(session)
    async with db.get_session() as s:
        return await _do_get_all(s)


async def get_school_by_name(
    name: str, session: AsyncSession | None = None
) -> SchoolResponse | None:
    """Get a school by exact name."""

    async def _do_get(s: AsyncSession):
        stmt = select(School).where(School.name == name).options(*SCHOOL_OPTIONS)
        school = (await s.execute(stmt)).scalars().first()
        return _to_school_response(school) if school else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_school_by_code(
    code: str, session: AsyncSession | None = None
) -> SchoolResponse | None:
    """Get a school by join code."""

    async def _do_get(s: AsyncSession):
        stmt = select(School).where(School.schoolCode == code).options(*SCHOOL_OPTIONS)
        school = (await s.execute(stmt)).scalar_one_or_none()
        return _to_school_response(school) if school else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)
