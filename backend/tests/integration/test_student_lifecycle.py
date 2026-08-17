"""Integration tests for Student onboarding, join requests by code, and sequential roll number assignment."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role, Student
from tests.factories.class_factory import create_class_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_student_joins_class_via_joincode_and_sequential_roll_numbers(
    auth_client_factory, db_session: AsyncSession
):
    """Verify students can submit join requests via joinCode and upon approval receive sequential roll numbers."""
    # 1. Setup School & Class
    principal_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.join@test.examarena.dev"
    )
    school = await create_school_factory(
        db_session, creator_user=principal_user, school_code="JOIN-001"
    )
    school_class = await create_class_factory(
        db_session,
        school=school,
        name="Grade 10-A",
        year="2026",
        section="A",
        join_code="TESTCODE",
        next_roll_no=1,
    )

    # 2. Setup two student users
    student_user_1 = await create_user_factory(
        db_session,
        role=Role.STUDENT,
        name="Student One",
        email="student1@test.examarena.dev",
    )
    student_user_2 = await create_user_factory(
        db_session,
        role=Role.STUDENT,
        name="Student Two",
        email="student2@test.examarena.dev",
    )
    await db_session.commit()

    student_1_client = await auth_client_factory(student_user_1)
    student_2_client = await auth_client_factory(student_user_2)
    principal_client = await auth_client_factory(principal_user)

    # 3. Student 1 requests to join using joinCode
    req1_resp = await student_1_client.post(
        "/api/v1/join-requests/join-by-code",
        json={"joinCode": "TESTCODE"},
    )
    assert req1_resp.status_code in (200, 201)
    req1_id = req1_resp.json()["id"]

    # 4. Student 2 requests to join using joinCode
    req2_resp = await student_2_client.post(
        "/api/v1/join-requests/join-by-code",
        json={"joinCode": "TESTCODE"},
    )
    assert req2_resp.status_code in (200, 201)
    req2_id = req2_resp.json()["id"]

    # 5. Principal approves Student 1 -> gets roll number "1"
    app1_resp = await principal_client.patch(
        f"/api/v1/join-requests/{req1_id}",
        json={"status": "APPROVED"},
    )
    assert app1_resp.status_code == 200

    result1 = await db_session.execute(
        select(Student).where(Student.userId == student_user_1.id)
    )
    st1 = result1.scalar_one_or_none()
    assert st1 is not None
    assert st1.rollNo == "1"

    # 6. Principal approves Student 2 -> gets roll number "2"
    app2_resp = await principal_client.patch(
        f"/api/v1/join-requests/{req2_id}",
        json={"status": "APPROVED"},
    )
    assert app2_resp.status_code == 200

    result2 = await db_session.execute(
        select(Student).where(Student.userId == student_user_2.id)
    )
    st2 = result2.scalar_one_or_none()
    assert st2 is not None
    assert st2.rollNo == "2"


@pytest.mark.asyncio
async def test_invalid_joincode_returns_404(
    auth_client_factory, db_session: AsyncSession
):
    """Verify trying to join with a non-existent join code returns 404 Not Found."""
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.invalid@test.examarena.dev"
    )
    await db_session.commit()

    client = await auth_client_factory(student_user)
    resp = await client.post(
        "/api/v1/join-requests/join-by-code",
        json={"joinCode": "NONEXIST"},
    )
    assert resp.status_code == 404
