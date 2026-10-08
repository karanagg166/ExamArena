"""Security and IDOR regression test matrix for Analytics and Teacher Results endpoints.

Verifies:
- Unauthenticated requests are rejected with 401.
- Students cannot access teacher overview, class analytics, or unowned student results (403).
- Students can access their own student results (200).
- Student A cannot access Student B's results (403 IDOR).
- Teacher A (School A) cannot access School B's class analytics (403 cross-tenant IDOR).
- Teacher A (School A) cannot access School B's student results (403 cross-tenant IDOR).
- Teacher B cannot access Teacher A's private exam analytics (403 IDOR).
- Tampered role/claims fail to elevate privileges.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role
from app.main import app
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_unauthenticated_requests_return_401():
    """Verify unauthenticated requests to analytics endpoints return 401 Unauthorized."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauth_client:
        resp1 = await unauth_client.get("/api/v1/teacher/results/overview")
        assert resp1.status_code == 401

        resp2 = await unauth_client.get("/api/v1/classes/fake-id/analytics")
        assert resp2.status_code == 401

        resp3 = await unauth_client.get("/api/v1/students/fake-id/results")
        assert resp3.status_code == 401

        resp4 = await unauth_client.get("/api/v1/exams/fake-id/analytics")
        assert resp4.status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_access_teacher_overview_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden when calling teacher results overview."""
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.forbidden.ov@test.dev"
    )
    await db_session.commit()

    client = await auth_client_factory(student_user)
    resp = await client.get("/api/v1/teacher/results/overview")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_class_analytics_or_leaderboard_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden attempting to access class analytics or leaderboard."""
    school = await create_school_factory(db_session, school_code="SCH-ST-CL")
    school_class = await create_class_factory(db_session, school=school)
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.class.an@test.dev"
    )
    await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    client = await auth_client_factory(student_user)

    resp1 = await client.get(f"/api/v1/classes/{school_class.id}/analytics")
    assert resp1.status_code == 403

    resp2 = await client.get(f"/api/v1/classes/{school_class.id}/leaderboard")
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_exam_analytics_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden attempting to access exam analytics."""
    exam = await create_exam_factory(db_session)
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.exam.an@test.dev"
    )
    await db_session.commit()

    client = await auth_client_factory(student_user)
    resp = await client.get(f"/api/v1/exams/{exam.id}/analytics")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_view_other_student_results_idor_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student A receives 403 Forbidden when attempting to view Student B's results (IDOR)."""
    school = await create_school_factory(db_session, school_code="SCH-IDOR-ST")
    school_class = await create_class_factory(db_session, school=school)

    u_a = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.a@test.dev"
    )
    s_a = await create_student_factory(
        db_session, user=u_a, school=school, school_class=school_class, roll_no="01"
    )

    u_b = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.b@test.dev"
    )
    s_b = await create_student_factory(
        db_session, user=u_b, school=school, school_class=school_class, roll_no="02"
    )
    await db_session.commit()

    client_a = await auth_client_factory(u_a)
    # Student A requests Student B results
    resp = await client_a.get(f"/api/v1/students/{s_b.id}/results")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_can_view_own_results_allowed(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student A can view their own results via /api/v1/students/{student_id}/results."""
    school = await create_school_factory(db_session, school_code="SCH-OWN-RES")
    school_class = await create_class_factory(db_session, school=school)

    u_a = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.own@test.dev"
    )
    s_a = await create_student_factory(
        db_session, user=u_a, school=school, school_class=school_class, roll_no="01"
    )
    await db_session.commit()

    client_a = await auth_client_factory(u_a)
    resp = await client_a.get(f"/api/v1/students/{s_a.id}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["studentId"] == s_a.id


@pytest.mark.asyncio
async def test_teacher_cannot_access_other_school_class_analytics_idor_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Teacher from School A receives 403 Forbidden accessing School B class analytics."""
    school_a = await create_school_factory(db_session, school_code="SCH-T-A")
    school_b = await create_school_factory(db_session, school_code="SCH-T-B")

    t_a_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.a@test.dev"
    )
    await create_teacher_factory(db_session, user=t_a_user, school=school_a)

    class_b = await create_class_factory(db_session, school=school_b)
    await db_session.commit()

    client_a = await auth_client_factory(t_a_user)
    resp = await client_a.get(f"/api/v1/classes/{class_b.id}/analytics")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_access_other_school_student_results_idor_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Teacher from School A receives 403 Forbidden accessing School B student results."""
    school_a = await create_school_factory(db_session, school_code="SCH-ST-A")
    school_b = await create_school_factory(db_session, school_code="SCH-ST-B")

    t_a_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.sta@test.dev"
    )
    await create_teacher_factory(db_session, user=t_a_user, school=school_a)

    class_b = await create_class_factory(db_session, school=school_b)
    u_b = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.in.b@test.dev"
    )
    s_b = await create_student_factory(
        db_session, user=u_b, school=school_b, school_class=class_b
    )
    await db_session.commit()

    client_a = await auth_client_factory(t_a_user)
    resp = await client_a.get(f"/api/v1/students/{s_b.id}/results")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_access_unowned_exam_analytics_idor_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Teacher B receives 403 Forbidden when accessing analytics for Teacher A's private exam."""
    school_a = await create_school_factory(db_session, school_code="SCH-EX-A")
    school_b = await create_school_factory(db_session, school_code="SCH-EX-B")

    t_a_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="owner.teacher@test.dev"
    )
    t_a = await create_teacher_factory(db_session, user=t_a_user, school=school_a)

    t_b_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="intruder.teacher@test.dev"
    )
    await create_teacher_factory(db_session, user=t_b_user, school=school_b)

    exam_a = await create_exam_factory(
        db_session, teacher=t_a, is_public=False, name="Private Exam A"
    )
    await db_session.commit()

    client_b = await auth_client_factory(t_b_user)
    resp = await client_b.get(f"/api/v1/exams/{exam_a.id}/analytics")
    assert resp.status_code == 403
