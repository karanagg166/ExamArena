"""Integration tests for RBAC, IDOR prevention, and cross-role authorization matrix."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role
from tests.factories.exam_factory import create_exam_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_student_cannot_create_exam_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden when attempting to create an exam."""
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.rbac@test.examarena.dev"
    )
    await db_session.commit()

    client = await auth_client_factory(student_user)

    exam_payload = {
        "name": "Unauthorized Exam",
        "description": "Student trying to create exam",
        "scheduledAt": "2026-10-01T10:00:00Z",
        "duration": 60,
        "maxMarks": 100,
        "subject": "MATHS",
        "type": "MIDTERM",
    }
    resp = await client.post("/api/v1/exams", json=exam_payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_create_question_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden when attempting to add questions."""
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.q@test.examarena.dev"
    )
    exam = await create_exam_factory(db_session)
    await db_session.commit()

    client = await auth_client_factory(student_user)

    question_payload = {
        "examId": exam.id,
        "questionNumber": 1,
        "text": "Unauthorized Question?",
        "marks": 5,
        "questionType": "MULTIPLE_CHOICE",
        "options": [
            {"text": "Option 1", "optionNumber": 1, "isCorrect": True},
            {"text": "Option 2", "optionNumber": 2, "isCorrect": False},
        ],
    }
    resp = await client.post("/api/v1/questions", json=question_payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_idor_cannot_edit_other_teacher_exam(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Teacher B cannot modify an exam created by Teacher A in a different school."""
    teacher_a = await create_teacher_factory(db_session)
    teacher_b_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.b@test.examarena.dev"
    )
    teacher_b = await create_teacher_factory(db_session, user=teacher_b_user)

    exam_a = await create_exam_factory(
        db_session, teacher=teacher_a, name="Teacher A Exam"
    )
    await db_session.commit()

    client_b = await auth_client_factory(teacher_b_user)

    resp = await client_b.patch(
        f"/api/v1/exams/{exam_a.id}",
        json={"name": "Hacked Exam Name"},
    )
    assert resp.status_code == 403

    # Verify Exam A name remains unchanged
    await db_session.refresh(exam_a)
    assert exam_a.name == "Teacher A Exam"
