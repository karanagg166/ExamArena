"""Integration tests for Bug 7: Scheduled exam start time boundary checks.

Invariants verified:
1. Attempting to start an exam 1 second before scheduledAt fails with HTTP 400.
2. Attempting to start an exam at the exact scheduledAt time succeeds with HTTP 201.
3. Attempting to start an exam 1 second after scheduledAt succeeds with HTTP 201.
4. Timezone-aware and timezone-naive datetimes are safely handled.
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_scheduled_exam_time_boundaries(
    auth_client_factory, db_session: AsyncSession, monkeypatch
):
    school = await create_school_factory(db_session, school_code="SCHED-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.sched@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    # 1. Exam scheduled for 2026-06-01 10:00:00 UTC
    scheduled_target = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    exam_aware = await create_exam_factory(
        db_session,
        teacher=teacher,
        scheduled_at=scheduled_target,
        is_published=True,
    )

    # 2. Exam with naive datetime
    scheduled_naive = datetime(2026, 6, 1, 10, 0, 0)
    exam_naive = await create_exam_factory(
        db_session,
        teacher=teacher,
        scheduled_at=scheduled_naive,
        is_published=True,
    )

    student_user_1 = await create_user_factory(
        db_session, role=Role.STUDENT, email="student1.sched@test.examarena.dev"
    )
    student_1 = await create_student_factory(
        db_session, user=student_user_1, school=school, school_class=school_class
    )

    student_user_2 = await create_user_factory(
        db_session, role=Role.STUDENT, email="student2.sched@test.examarena.dev"
    )
    student_2 = await create_student_factory(
        db_session, user=student_user_2, school=school, school_class=school_class
    )

    student_user_3 = await create_user_factory(
        db_session, role=Role.STUDENT, email="student3.sched@test.examarena.dev"
    )
    student_3 = await create_student_factory(
        db_session, user=student_user_3, school=school, school_class=school_class
    )
    await db_session.commit()

    client_1 = await auth_client_factory(student_user_1)
    client_2 = await auth_client_factory(student_user_2)
    client_3 = await auth_client_factory(student_user_3)

    # Case A: 1 second BEFORE scheduled start time -> 400
    mocked_before = scheduled_target - timedelta(seconds=1)

    class MockDatetimeBefore(datetime):
        @classmethod
        def now(cls, tz=None):
            return mocked_before

    monkeypatch.setattr("app.attempts.crud.datetime", MockDatetimeBefore)

    resp_before = await client_1.post(
        "/api/v1/attempts/start",
        json={"examId": str(exam_aware.id)},
    )
    assert resp_before.status_code == 400
    assert "scheduled" in resp_before.json()["detail"].lower()

    # Case B: EXACT scheduled start time -> 201
    class MockDatetimeExact(datetime):
        @classmethod
        def now(cls, tz=None):
            return scheduled_target

    monkeypatch.setattr("app.attempts.crud.datetime", MockDatetimeExact)

    resp_exact = await client_1.post(
        "/api/v1/attempts/start",
        json={"examId": str(exam_aware.id)},
    )
    assert resp_exact.status_code == 201
    assert resp_exact.json()["examId"] == str(exam_aware.id)

    # Case C: 1 second AFTER scheduled start time -> 201
    mocked_after = scheduled_target + timedelta(seconds=1)

    class MockDatetimeAfter(datetime):
        @classmethod
        def now(cls, tz=None):
            return mocked_after

    monkeypatch.setattr("app.attempts.crud.datetime", MockDatetimeAfter)

    resp_after = await client_2.post(
        "/api/v1/attempts/start",
        json={"examId": str(exam_aware.id)},
    )
    assert resp_after.status_code == 201

    # Case D: Timezone-naive scheduled time handled safely when now is after
    resp_naive = await client_3.post(
        "/api/v1/attempts/start",
        json={"examId": str(exam_naive.id)},
    )
    assert resp_naive.status_code == 201
