"""User test factory for generating database User records."""

import uuid
from datetime import UTC, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role, User
from app.core.security import hash_password


async def create_user_factory(
    session: AsyncSession,
    *,
    email: str | None = None,
    name: str = "Test User",
    password: str = "TestPass123!",
    role: Role = Role.STUDENT,
    phone_no: str = "9876543210",
    city: str = "New Delhi",
    state: str = "Delhi",
    country: str = "India",
    pincode: str = "110001",
    date_of_birth: datetime | None = None,
) -> User:
    """Create and persist a User record in the test database."""
    unique_suffix = uuid.uuid4().hex[:8]
    final_email = email or f"user_{unique_suffix}@test.examarena.dev"
    final_dob = date_of_birth or datetime(2000, 1, 1, tzinfo=UTC)
    hashed_pwd = hash_password(password)

    user = User(
        name=name,
        email=final_email,
        password=hashed_pwd,
        phoneNo=phone_no,
        role=role,
        dateOfBirth=final_dob,
        city=city,
        state=state,
        country=country,
        pincode=pincode,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user
