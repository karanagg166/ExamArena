"""School and Principal test factory for generating database records."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Principal, Role, School, SchoolType, Teacher, User
from tests.factories.user_factory import create_user_factory


async def create_school_factory(
    session: AsyncSession,
    *,
    creator_user: User | None = None,
    name: str = "Test Arena Academy",
    school_code: str | None = None,
    school_type: SchoolType = SchoolType.PUBLIC,
    address: str = "123 Education Lane",
    city: str = "New Delhi",
    state: str = "Delhi",
    country: str = "India",
    pincode: str = "110001",
    email: str | None = None,
    website: str = "https://testarena.edu",
    phone_no: str = "9876543210",
) -> School:
    """Create and persist a School record with an associated Principal user if none provided."""
    unique_suffix = uuid.uuid4().hex[:6].upper()
    final_code = school_code or f"SCH-{unique_suffix}"

    if not creator_user:
        creator_user = await create_user_factory(
            session,
            role=Role.PRINCIPAL,
            name=f"Principal {unique_suffix}",
            email=f"principal_{unique_suffix.lower()}@test.examarena.dev",
        )

    school = School(
        name=name,
        createdBy=creator_user.id,
        address=address,
        city=city,
        state=state,
        country=country,
        pincode=pincode,
        schoolCode=final_code,
        type=school_type,
        email=email or f"contact@{final_code.lower()}.edu",
        website=website,
        phoneNo=phone_no,
    )
    session.add(school)
    await session.flush()
    await session.refresh(school)

    # Automatically create/link Teacher and Principal profile for the creator
    teacher = Teacher(
        userId=creator_user.id,
        experience=5,
        department="Administration",
        qualification='["MASTERS"]',
        subjects='["MATHS"]',
        schoolId=school.id,
    )
    session.add(teacher)
    await session.flush()
    await session.refresh(teacher)

    principal = Principal(
        teacherId=teacher.id,
        experience=5,
        schoolId=school.id,
    )
    session.add(principal)
    await session.flush()
    await session.refresh(principal)

    return school
