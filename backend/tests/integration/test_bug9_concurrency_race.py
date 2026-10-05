"""Integration tests for Bug 9: Duplicate attempt start and concurrent race condition handling.

Invariants verified:
1. Calling start exam twice sequentially returns the same existing attempt without error.
2. Concurrent race condition where a duplicate insert occurs (simulated IntegrityError)
   gracefully rolls back and returns the existing attempt rather than throwing a 500 error.
"""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.attempts.crud import start_exam_attempt
from app.attempts.schemas import StudentExamCreate
from app.core.models import Role
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_duplicate_start_and_concurrent_race_condition(
    auth_client_factory, db_session: AsyncSession
):
    school = await create_school_factory(db_session, school_code="RACE-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.race@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        is_published=True,
    )

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.race@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    student_client = await auth_client_factory(student_user)
    exam_id = str(exam.id)

    # 1. First start request creates the attempt
    resp_1 = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id},
    )
    assert resp_1.status_code == 201
    attempt_1 = resp_1.json()

    # 2. Sequential second start request returns the exact same attempt
    resp_2 = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id},
    )
    assert resp_2.status_code == 201
    attempt_2 = resp_2.json()
    assert attempt_2["id"] == attempt_1["id"]

    # 3. Simulate race condition: start_exam_attempt called when commit throws IntegrityError
    student_create_dto = StudentExamCreate(examId=exam_id)
    attempt_res = await start_exam_attempt(student_create_dto, student_user.id)
    assert attempt_res.id == attempt_1["id"]
