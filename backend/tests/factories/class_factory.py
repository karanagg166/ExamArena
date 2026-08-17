"""SchoolClass test factory for generating database records."""

import secrets
import string
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import School, SchoolClass
from tests.factories.school_factory import create_school_factory


async def create_class_factory(
    session: AsyncSession,
    *,
    school: School | None = None,
    name: str = "Class 10-A",
    year: str = "2026",
    section: str = "A",
    join_code: str | None = None,
    next_roll_no: int = 1,
) -> SchoolClass:
    """Create and persist a SchoolClass in the test database."""
    if not school:
        school = await create_school_factory(session)

    if not join_code:
        alphabet = string.ascii_uppercase + string.digits
        join_code = "".join(secrets.choice(alphabet) for _ in range(8))

    school_class = SchoolClass(
        name=name,
        year=year,
        section=section,
        schoolId=school.id,
        joinCode=join_code,
        nextRollNo=next_roll_no,
    )
    session.add(school_class)
    await session.flush()
    await session.refresh(school_class)
    return school_class
