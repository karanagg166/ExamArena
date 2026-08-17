"""Teacher test factory for generating teacher and teacher-class assignments."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Role,
    School,
    SchoolClass,
    Subject,
    Teacher,
    TeacherClass,
    User,
)
from tests.factories.user_factory import create_user_factory


async def create_teacher_factory(
    session: AsyncSession,
    *,
    user: User | None = None,
    school: School | None = None,
    experience: int = 4,
    department: str = "Science",
    qualification: str = '["BACHELORS"]',
    subjects: str = '["SCIENCE"]',
) -> Teacher:
    """Create and persist a Teacher profile in the test database."""
    unique_suffix = uuid.uuid4().hex[:6]
    if not user:
        user = await create_user_factory(
            session,
            role=Role.TEACHER,
            name=f"Teacher {unique_suffix}",
            email=f"teacher_{unique_suffix}@test.examarena.dev",
        )

    teacher = Teacher(
        userId=user.id,
        experience=experience,
        department=department,
        qualification=qualification,
        subjects=subjects,
        schoolId=school.id if school else None,
    )
    session.add(teacher)
    await session.flush()
    await session.refresh(teacher)
    return teacher


async def assign_teacher_to_class_factory(
    session: AsyncSession,
    *,
    teacher: Teacher,
    school_class: SchoolClass,
    subject: Subject = Subject.SCIENCE,
) -> TeacherClass:
    """Assign a teacher to a class with a specific subject."""
    teacher_class = TeacherClass(
        teacherId=teacher.id,
        classId=school_class.id,
        subject=subject,
    )
    session.add(teacher_class)
    await session.flush()
    await session.refresh(teacher_class)
    return teacher_class
