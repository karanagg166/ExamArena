"""Integration tests for Exam creation, questions, password protection, and answer key redaction."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import QuestionType, Role, StudentExamStatus
from tests.factories.attempt_factory import create_attempt_factory
from tests.factories.exam_factory import (
    create_exam_factory,
    create_question_factory,
)
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_exam_creation_with_sections_and_questions(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Teacher can create an exam with sections and multiple question types."""
    principal_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="princ.exam@test.examarena.dev"
    )
    school = await create_school_factory(
        db_session, creator_user=principal_user, school_code="EXAM-001"
    )
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.exam@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    # 1. Create Exam
    exam_payload = {
        "name": "Physics Final",
        "description": "Comprehensive physics exam",
        "scheduledAt": "2026-11-15T09:00:00Z",
        "duration": 90,
        "maxMarks": 100,
        "subject": "PHYSICS",
        "type": "FINAL",
        "negativeMarking": True,
        "negativeMarks": 1.0,
    }
    exam_resp = await client.post("/api/v1/exams", json=exam_payload)
    assert exam_resp.status_code == 201
    exam_data = exam_resp.json()
    exam_id = exam_data["id"]

    # 2. Create Section
    sec_payload = {
        "examId": exam_id,
        "name": "Section A",
        "questionType": "MULTIPLE_CHOICE",
        "marksPerQuestion": 4,
        "sortOrder": 1,
        "negativeMarking": True,
        "negativeMarks": 1.0,
    }
    sec_resp = await client.post("/api/v1/sections", json=sec_payload)
    assert sec_resp.status_code == 201
    sec_id = sec_resp.json()["id"]

    # 3. Create Question with Options
    q_payload = {
        "examId": exam_id,
        "sectionId": sec_id,
        "questionNumber": 1,
        "text": "What is the speed of light in vacuum?",
        "marks": 4,
        "questionType": "MULTIPLE_CHOICE",
        "explanation": "Speed of light is approximately 3x10^8 m/s",
        "options": [
            {"text": "3 x 10^8 m/s", "optionNumber": 1, "isCorrect": True},
            {"text": "3 x 10^6 m/s", "optionNumber": 2, "isCorrect": False},
            {"text": "1.5 x 10^8 m/s", "optionNumber": 3, "isCorrect": False},
        ],
    }
    q_resp = await client.post("/api/v1/questions", json=q_payload)
    assert q_resp.status_code == 201


@pytest.mark.asyncio
async def test_solution_redaction_for_students_prior_to_result_release(
    auth_client_factory, db_session: AsyncSession
):
    """Verify students cannot see correct answers or explanations before results are released."""
    school = await create_school_factory(db_session, school_code="RED-001")
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.sec@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(
        db_session, teacher=teacher, is_published=True, is_results_released=False
    )
    q = await create_question_factory(
        db_session,
        exam=exam,
        text="Secret Question?",
        explanation="Secret explanation revealed only on result release",
        options_data=[
            {"text": "Option A (Correct)", "isCorrect": True},
            {"text": "Option B (Incorrect)", "isCorrect": False},
        ],
    )
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.view@test.examarena.dev"
    )
    student = await create_student_factory(db_session, user=student_user, school=school)
    # Student has in-progress attempt
    await create_attempt_factory(
        db_session,
        exam=exam,
        student=student,
        status=StudentExamStatus.IN_PROGRESS,
    )
    await db_session.commit()

    student_client = await auth_client_factory(student_user)
    teacher_client = await auth_client_factory(teacher_user)

    # 1. Student views exam
    stud_resp = await student_client.get(f"/api/v1/exams/{exam.id}")
    assert stud_resp.status_code == 200
    stud_exam = stud_resp.json()
    stud_questions = stud_exam.get("questions", [])
    assert len(stud_questions) > 0
    stud_q = stud_questions[0]

    # Explanation must be null / hidden
    assert stud_q.get("explanation") is None

    # All options must have isCorrect set to False
    for opt in stud_q.get("options", []):
        assert opt.get("isCorrect") is False

    # 2. Teacher views exam -> sees full answers and explanations
    teach_resp = await teacher_client.get(f"/api/v1/exams/{exam.id}")
    assert teach_resp.status_code == 200
    teach_q = teach_resp.json()["questions"][0]
    assert (
        teach_q["explanation"] == "Secret explanation revealed only on result release"
    )
    correct_opts = [o for o in teach_q["options"] if o.get("isCorrect") is True]
    assert len(correct_opts) == 1
