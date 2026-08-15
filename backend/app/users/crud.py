from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.core.models import User
from app.core.security import hash_password, verify_password
from app.users.schemas import UserRequest, UserUpdate


async def get_user_by_email(
    email: str, session: AsyncSession | None = None
) -> User | None:
    """Retrieve a user by their email address."""
    if session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    async with db.get_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def get_user_by_id(
    user_id: str, session: AsyncSession | None = None
) -> User | None:
    """Retrieve a user by their unique database ID."""
    if session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    async with db.get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def create_user(
    user_data: UserRequest, session: AsyncSession | None = None
) -> User:
    """
    Creates ONLY the base User account.
    Role-specific profiles (Student, Teacher) must be created in a later step.
    """
    hashed_password = hash_password(user_data.password)
    data_dict = user_data.model_dump(exclude={"password", "role"})
    data_dict["password"] = hashed_password
    data_dict["role"] = user_data.role.value

    async def _do_create(s: AsyncSession):
        user = User(**data_dict)
        s.add(user)
        await s.commit()
        await s.refresh(user)
        return user

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def update_user(
    user_id: str, user_data: UserUpdate, session: AsyncSession | None = None
) -> User | None:
    """Safely updates only the fields the user provided."""
    update_dict = user_data.model_dump(exclude_unset=True)
    if "password" in update_dict and update_dict["password"]:
        update_dict["password"] = hash_password(update_dict["password"])

    async def _do_update(s: AsyncSession):
        user = (
            await s.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if not user:
            return None
        if update_dict:
            for key, value in update_dict.items():
                setattr(user, key, value)
            await s.commit()
            await s.refresh(user)
        return user

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def change_user_password(
    user_id: str,
    current_password: str,
    new_password: str,
    session: AsyncSession | None = None,
) -> bool:
    """Changes the password for a specified user after verifying current password."""
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long",
        )

    async def _do_change(s: AsyncSession):
        user = (
            await s.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if not verify_password(current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )

        user.password = hash_password(new_password)
        await s.commit()
        return True

    if session:
        return await _do_change(session)
    async with db.get_session() as s:
        return await _do_change(s)
