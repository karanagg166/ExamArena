"""Integration tests for Teacher onboarding, school join requests, and class assignments."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Role,
    Subject,
    Teacher,
    TeacherClass,
)
from tests.factories.class_factory import create_class_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_teacher_school_join_request_approval_flow(
    auth_client_factory, db_session: AsyncSession
):
    """Verify teacher can request to join school and principal approval links teacher to school."""
    # 1. Setup School with Principal
    principal_user = await create_user_factory(
        db_session,
        name="Headmaster",
        email="headmaster@academy.edu",
        role=Role.PRINCIPAL,
    )
    school = await create_school_factory(
        db_session,
        creator_user=principal_user,
        name="Hogwarts Academy",
        school_code="HOG-001",
    )

    # 2. Setup Unaffiliated Teacher
    teacher_user = await create_user_factory(
        db_session,
        name="Severus Snape",
        email="snape@test.examarena.dev",
        role=Role.TEACHER,
    )
    teacher = await create_teacher_factory(
        db_session,
        user=teacher_user,
        school=None,
        department="Potions",
    )
    await db_session.commit()

    teacher_client = await auth_client_factory(teacher_user)
    principal_client = await auth_client_factory(principal_user)

    # 3. Teacher requests to join school
    req_resp = await teacher_client.post(
        "/api/v1/teacher-requests/school",
        json={"schoolId": school.id},
    )
    assert req_resp.status_code in (200, 201)
    req_id = req_resp.json()["id"]

    # 4. Principal views school requests
    list_resp = await principal_client.get(
        f"/api/v1/teacher-requests/school-requests/{school.id}"
    )
    assert list_resp.status_code == 200

    # 5. Principal approves request
    decide_resp = await principal_client.patch(
        f"/api/v1/teacher-requests/school-requests/{req_id}",
        json={"status": "APPROVED"},
    )
    assert decide_resp.status_code == 200

    # 6. Verify teacher is now linked to school in database
    await db_session.refresh(teacher)
    assert teacher.schoolId == school.id


@pytest.mark.asyncio
async def test_assign_teacher_to_class_with_subject(
    auth_client_factory, db_session: AsyncSession
):
    """Verify assigning a teacher to a class."""
    principal_user = await create_user_factory(
        db_session,
        role=Role.PRINCIPAL,
        email="principal.classes@test.examarena.dev",
    )
    school = await create_school_factory(
        db_session, creator_user=principal_user, school_code="CLS-001"
    )
    school_class = await create_class_factory(
        db_session, school=school, name="Grade 10 Science", section="A"
    )
    teacher_user = await create_user_factory(
        db_session,
        role=Role.TEACHER,
        email="science.teacher@test.examarena.dev",
    )
    teacher = await create_teacher_factory(
        db_session,
        user=teacher_user,
        school=school,
    )
    await db_session.commit()

    principal_client = await auth_client_factory(principal_user)

    assign_payload = {
        "teacherId": teacher.id,
    }
    assign_resp = await principal_client.post(
        f"/api/v1/classes/{school_class.id}/assign-teacher",
        json=assign_payload,
    )
    assert assign_resp.status_code in (200, 201)

    # Verify TeacherClass in database
    result = await db_session.execute(
        select(TeacherClass).where(
            TeacherClass.teacherId == teacher.id,
            TeacherClass.classId == school_class.id,
        )
    )
    tc = result.scalar_one_or_none()
    assert tc is not None
