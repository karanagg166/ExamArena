from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import Principal, Role, Teacher, User
from app.principals.schemas import PrincipalUpdate

PRINCIPAL_OPTIONS = [
    selectinload(Principal.teacher).selectinload(Teacher.user),
    selectinload(Principal.school),
]


async def get_principal_by_teacher_id(
    teacher_id: str, session: AsyncSession | None = None
):
    """Get a principal by teacher ID."""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Principal)
            .where(Principal.teacherId == teacher_id)
            .options(*PRINCIPAL_OPTIONS)
        )
        return (await s.execute(stmt)).scalar_one_or_none()

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def create_principal(
    teacher_id: str,
    experience: int = 0,
    school_id: str | None = None,
    session: AsyncSession | None = None,
):
    """Create a principal linked to an existing teacher."""

    async def _do_create(s: AsyncSession):
        teacher_stmt = select(Teacher).where(Teacher.id == teacher_id)
        teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
        if teacher:
            user_stmt = select(User).where(User.id == teacher.userId)
            user = (await s.execute(user_stmt)).scalar_one_or_none()
            if user:
                user.role = Role.PRINCIPAL

        principal = Principal(
            teacherId=teacher_id,
            experience=experience,
            schoolId=school_id,
        )
        s.add(principal)
        await s.commit()

        stmt = (
            select(Principal)
            .where(Principal.teacherId == teacher_id)
            .options(*PRINCIPAL_OPTIONS)
        )
        return (await s.execute(stmt)).scalar_one_or_none()

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def update_principal(
    teacher_id: str,
    principal_data: PrincipalUpdate,
    session: AsyncSession | None = None,
):
    """Update a principal by teacher ID."""
    update_dict = principal_data.model_dump(exclude_unset=True)

    async def _do_update(s: AsyncSession):
        stmt = select(Principal).where(Principal.teacherId == teacher_id)
        principal = (await s.execute(stmt)).scalar_one_or_none()
        if principal and update_dict:
            for k, v in update_dict.items():
                setattr(principal, k, v)
            await s.commit()

        res_stmt = (
            select(Principal)
            .where(Principal.teacherId == teacher_id)
            .options(*PRINCIPAL_OPTIONS)
        )
        return (await s.execute(res_stmt)).scalar_one_or_none()

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_principal(teacher_id: str, session: AsyncSession | None = None):
    """Delete a principal by teacher ID."""

    async def _do_delete(s: AsyncSession):
        stmt = select(Principal).where(Principal.teacherId == teacher_id)
        principal = (await s.execute(stmt)).scalar_one_or_none()
        if principal:
            await s.delete(principal)
            await s.commit()
            return principal
        return None

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)
