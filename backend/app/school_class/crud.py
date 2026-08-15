import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.core.models import SchoolClass
from app.school.crud import get_school_by_user_id
from app.school_class.schemas import (
    SchoolClassCreateRequest,
    SchoolClassResponse,
    SchoolClassUpdateRequest,
)


def generate_join_code() -> str:
    """Generate an easily shareable, case-insensitive class join code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


async def create_school_class(
    class_data: SchoolClassCreateRequest,
    user_id: str,
    session: AsyncSession | None = None,
) -> SchoolClassResponse | None:
    """Create a class for the authenticated user's school."""
    school = await get_school_by_user_id(user_id, session=session)
    if not school:
        return None

    data_dict = class_data.model_dump()
    data_dict["schoolId"] = school.id

    async def _do_create(s: AsyncSession):
        # A database unique constraint is the final guard; this pre-check makes a
        # (very unlikely) random collision recoverable without exposing an error.
        for _ in range(10):
            join_code = generate_join_code()
            exists = await s.scalar(
                select(SchoolClass.id).where(SchoolClass.joinCode == join_code)
            )
            if not exists:
                data_dict["joinCode"] = join_code
                break
        else:
            raise RuntimeError("Unable to generate a unique class join code")

        school_class = SchoolClass(**data_dict)
        s.add(school_class)
        await s.commit()
        await s.refresh(school_class)
        return SchoolClassResponse.model_validate(school_class)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_school_classes_by_school_id(
    school_id: str, session: AsyncSession | None = None
) -> list[SchoolClassResponse]:
    """Get all classes for a school."""

    async def _do_get(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.schoolId == school_id)
        classes = (await s.execute(stmt)).scalars().all()
        return [SchoolClassResponse.model_validate(c) for c in classes]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_school_class_by_id(
    class_id: str, session: AsyncSession | None = None
) -> SchoolClassResponse | None:
    """Get a specific class by its ID."""

    async def _do_get(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(stmt)).scalar_one_or_none()
        if not school_class:
            return None
        return SchoolClassResponse.model_validate(school_class)

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def update_school_class(
    class_id: str,
    class_data: SchoolClassUpdateRequest,
    user_id: str,
    session: AsyncSession | None = None,
) -> SchoolClassResponse | None:
    """Update a class that belongs to the authenticated user's school."""
    update_dict = class_data.model_dump(exclude_unset=True)
    if not update_dict:
        return None

    school = await get_school_by_user_id(user_id, session=session)
    if not school:
        return None

    async def _do_update(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(stmt)).scalar_one_or_none()
        if not school_class or school_class.schoolId != school.id:
            return None

        for k, v in update_dict.items():
            setattr(school_class, k, v)
        await s.commit()
        await s.refresh(school_class)
        return SchoolClassResponse.model_validate(school_class)

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_school_class(
    class_id: str, user_id: str, session: AsyncSession | None = None
) -> bool:
    """Delete a class that belongs to the authenticated user's school."""
    school = await get_school_by_user_id(user_id, session=session)
    if not school:
        return False

    async def _do_delete(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(stmt)).scalar_one_or_none()
        if not school_class or school_class.schoolId != school.id:
            return False

        await s.delete(school_class)
        await s.commit()
        return True

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)
