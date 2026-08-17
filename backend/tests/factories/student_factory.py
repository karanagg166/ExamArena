"""Student test factory for generating student database records."""

import uuid
from datetime import UTC, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role, School, SchoolClass, Student, User
from tests.factories.class_factory import create_class_factory
from tests.factories.user_factory import create_user_factory


async def create_student_factory(
    session: AsyncSession,
    *,
    user: User | None = None,
    school: School | None = None,
    school_class: SchoolClass | None = None,
    roll_no: str | None = None,
    parent_name: str = "Parent User",
    parent_email: str = "parent@test.examarena.dev",
) -> Student:
    """Create and persist a Student profile in the test database."""
    unique_suffix = uuid.uuid4().hex[:6]
    if not school_class:
        school_class = await create_class_factory(session, school=school)

    if not user:
        user = await create_user_factory(
            session,
            role=Role.STUDENT,
            name=f"Student {unique_suffix}",
            email=f"student_{unique_suffix}@test.examarena.dev",
        )

    final_roll_no = roll_no or str(school_class.nextRollNo)
    school_class.nextRollNo += 1

    student = Student(
        userId=user.id,
        rollNo=final_roll_no,
        classId=school_class.id,
        schoolId=school_class.schoolId,
        parentName=parent_name,
        parentEmail=parent_email,
        dateOfAdmission=datetime.now(UTC),
    )
    session.add(student)
    await session.flush()
    await session.refresh(student)
    return student
