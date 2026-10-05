"""Integration tests for Bug 9: Duplicate attempt start and concurrent race condition handling.

Invariants verified:
1. Calling start exam twice sequentially returns the same existing attempt without error.
2. Concurrent race condition where a duplicate insert occurs (simulated IntegrityError)
   gracefully rolls back and returns the existing competing attempt rather than throwing a 500 error.
"""

from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.attempts.crud import start_exam_attempt
from app.attempts.schemas import StudentExamCreate
from app.core.models import Role, StudentExam, StudentExamStatus
from tests.conftest import TestAsyncSessionLocal
from tests.factories.attempt_factory import create_attempt_factory
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_duplicate_start_returns_existing_attempt(
    auth_client_factory, db_session: AsyncSession
):
    """Sequential duplicate start calls must return the same attempt and keep exactly 1 DB row."""
    school = await create_school_factory(db_session, school_code="RACE-DUP-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.race.dup@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        is_published=True,
    )

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.race.dup@test.examarena.dev"
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

    # 3. Assert exactly one StudentExam row exists in the database
    async with TestAsyncSessionLocal() as verify_session:
        stmt = select(StudentExam).where(
            StudentExam.studentId == student.id,
            StudentExam.examId == exam.id,
        )
        all_attempts = (await verify_session.execute(stmt)).scalars().all()
        assert len(all_attempts) == 1
        assert str(all_attempts[0].id) == attempt_1["id"]


@pytest.mark.asyncio
async def test_integrity_error_race_returns_competing_attempt(
    db_session: AsyncSession,
):
    """Simulate exact race condition:

    Request A SELECT: no attempt exists
    Request B: creates and commits attempt first
    Request A INSERT: commit raises IntegrityError due to UNIQUE(studentId, examId)
    Request A: rollback called
    Request A SELECT: retrieves competing attempt created by Request B
    Request A: returns competing attempt successfully without 500 error
    """
    school = await create_school_factory(db_session, school_code="RACE-INTEG-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.race.integ@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        is_published=True,
    )

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.race.integ@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    exam_id = str(exam.id)
    student_create_dto = StudentExamCreate(examId=exam_id)

    # Use a real session from TestAsyncSessionLocal
    async with TestAsyncSessionLocal() as session_a:
        original_commit = session_a.commit
        rollback_spy = AsyncMock(wraps=session_a.rollback)
        session_a.rollback = rollback_spy

        competing_attempt_id: str | None = None

        async def racing_commit():
            nonlocal competing_attempt_id
            # Competing Request B: creates attempt in a separate session and commits
            async with TestAsyncSessionLocal() as session_b:
                competing_attempt = await create_attempt_factory(
                    session_b,
                    exam=exam,
                    student=student,
                    status=StudentExamStatus.IN_PROGRESS,
                )
                await session_b.commit()
                competing_attempt_id = str(competing_attempt.id)

            # Now session_a attempts to commit its duplicate attempt.
            # In PostgreSQL, this violates UNIQUE(studentId, examId) and raises IntegrityError!
            await original_commit()

        session_a.commit = racing_commit

        # Call start_exam_attempt with session_a
        recovered_attempt = await start_exam_attempt(
            student_create_dto, student_user.id, session=session_a
        )

        # Invariants verified:
        # 1. IntegrityError was caught and rollback was invoked on session_a
        assert rollback_spy.await_count >= 1

        # 2. Competing attempt created by Request B was retrieved and returned
        assert competing_attempt_id is not None
        assert str(recovered_attempt.id) == competing_attempt_id

    # 3. Exactly one attempt exists in the database
    async with TestAsyncSessionLocal() as verify_session:
        stmt = select(StudentExam).where(
            StudentExam.studentId == student.id,
            StudentExam.examId == exam.id,
        )
        attempts_in_db = (await verify_session.execute(stmt)).scalars().all()
        assert len(attempts_in_db) == 1
        assert str(attempts_in_db[0].id) == competing_attempt_id
