"""Integration tests for Bug 1 & Bug 4: Result redaction before teacher releases results.

Invariants verified:
1. Internal grading occurs upon submission and stores actual score in DB.
2. HTTP response returned to student on submit hides marksObtained, marksAwarded, isCorrect, feedback.
3. GET /api/v1/attempts/{id} by student hides marksObtained, marksAwarded, isCorrect, feedback before release.
4. GET /api/v1/students/{id}/exams by student hides marksObtained and percentage before release.
5. Staff access to student exam history preserves internal scores.
6. After teacher calls POST /api/v1/exams/{id}/release-results:
   - Student attempt response reveals marksObtained, marksAwarded, isCorrect.
   - Student exam endpoint reveals correct option flags and question explanations.
   - Student exam history reveals marksObtained and percentage.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import (
    Correctness,
    QuestionType,
    Role,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
)
from tests.factories.attempt_factory import create_attempt_factory, create_attempt_answer_factory
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory, create_question_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_result_redaction_before_and_after_release(
    auth_client_factory, db_session: AsyncSession
):
    school = await create_school_factory(db_session, school_code="REDACT-001")
    school_class = await create_class_factory(db_session, school=school)

    # Teacher setup
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.redaction@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    # Published exam with results not yet released
    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        max_marks=10,
        is_published=True,
        is_results_released=False,
    )

    # MCQ question (worth 10 marks)
    q1 = await create_question_factory(
        db_session,
        exam=exam,
        question_type=QuestionType.MULTIPLE_CHOICE,
        marks=10.0,
        text="What is the capital of France?",
        explanation="Paris is the capital of France.",
        options_data=[
            {"text": "Paris", "isCorrect": True},
            {"text": "London", "isCorrect": False},
        ],
    )
    from app.core.models import QuestionOption

    opts_res = await db_session.execute(
        select(QuestionOption).where(QuestionOption.questionId == q1.id)
    )
    all_opts = opts_res.scalars().all()
    correct_opt = [opt for opt in all_opts if opt.isCorrect][0]

    # Student setup
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.redaction@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )

    # Initial In-Progress Attempt
    attempt = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student,
        status=StudentExamStatus.IN_PROGRESS,
    )
    db_answer = await create_attempt_answer_factory(
        db_session,
        attempt=attempt,
        question=q1,
    )
    await db_session.commit()

    student_client = await auth_client_factory(student_user)
    teacher_client = await auth_client_factory(teacher_user)

    attempt_id = str(attempt.id)
    student_id = str(student.id)
    exam_id = str(exam.id)

    # ── Step 1: Student submits the exam attempt with the correct answer ──────
    submit_payload = {
        "id": attempt_id,
        "answers": [
            {
                "id": str(db_answer.id),
                "textAnswer": None,
                "selectedOptions": [{"optionId": str(correct_opt.id)}],
            }
        ],
    }
    submit_resp = await student_client.post("/api/v1/attempts/submit", json=submit_payload)
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()

    # Verify student response does NOT reveal sensitive grading information
    assert submit_data["status"] in ("SUBMITTED", "GRADED")
    assert submit_data["marksObtained"] is None, "Student must not receive marksObtained before release"
    assert submit_data["answers"][0]["marksAwarded"] is None
    assert submit_data["answers"][0]["isCorrect"] is None
    assert submit_data["answers"][0]["feedback"] is None
    assert submit_data["answers"][0]["gradingStatus"] is None

    # ── Step 2: Verify database directly contains internal graded score ────────
    from tests.conftest import TestAsyncSessionLocal

    stmt = (
        select(StudentExam)
        .where(StudentExam.id == attempt_id)
        .options(
            selectinload(StudentExam.answers).selectinload(StudentExamAnswer.selectedOptions)
        )
    )
    async with TestAsyncSessionLocal() as verify_session:
        db_exam_res = (await verify_session.execute(stmt)).scalar_one()
        assert db_exam_res.marksObtained == 10.0, "Database must store actual graded marks"
        assert db_exam_res.answers[0].marksAwarded == 10.0
        assert db_exam_res.answers[0].isCorrect == Correctness.FULLY_CORRECT

    # ── Step 3: GET /api/v1/attempts/{id} by student before release ───────────
    get_attempt_resp = await student_client.get(f"/api/v1/attempts/{attempt_id}")
    assert get_attempt_resp.status_code == 200
    att_data = get_attempt_resp.json()
    assert att_data["marksObtained"] is None
    assert att_data["answers"][0]["marksAwarded"] is None
    assert att_data["answers"][0]["isCorrect"] is None
    assert att_data["answers"][0]["feedback"] is None
    assert att_data["answers"][0]["gradingStatus"] is None

    # ── Step 4: GET /api/v1/students/{id}/exams by student before release ─────
    history_resp = await student_client.get(f"/api/v1/students/{student_id}/exams")
    assert history_resp.status_code == 200
    history_items = history_resp.json()
    assert len(history_items) == 1
    assert history_items[0]["isResultsReleased"] is False
    assert history_items[0]["marksObtained"] is None, "Score must be redacted for student"
    assert history_items[0]["percentage"] is None, "Percentage must be redacted for student"

    # Staff access before release preserves internal scores
    teacher_history_resp = await teacher_client.get(f"/api/v1/students/{student_id}/exams")
    assert teacher_history_resp.status_code == 200
    teacher_history_items = teacher_history_resp.json()
    assert teacher_history_items[0]["marksObtained"] == 10.0
    assert teacher_history_items[0]["percentage"] == 100.0

    # ── Step 5: Check exam details endpoint before release ────────────────────
    exam_student_resp = await student_client.get(f"/api/v1/exams/{exam_id}")
    assert exam_student_resp.status_code == 200
    exam_data = exam_student_resp.json()
    # Before release, solutions & explanations are hidden
    for q in exam_data.get("questions", []):
        assert q["explanation"] is None
        for opt in q["options"]:
            assert opt["isCorrect"] is False

    # ── Step 6: Teacher releases results ──────────────────────────────────────
    rel_resp = await teacher_client.post(f"/api/v1/exams/{exam_id}/release-results")
    assert rel_resp.status_code == 200
    assert rel_resp.json()["isResultsReleased"] is True

    # ── Step 7: Student accesses results after release ─────────────────────────
    # A) Attempt endpoint now reveals score and correctness
    after_attempt_resp = await student_client.get(f"/api/v1/attempts/{attempt_id}")
    assert after_attempt_resp.status_code == 200
    after_att_data = after_attempt_resp.json()
    assert after_att_data["marksObtained"] == 10.0
    assert after_att_data["answers"][0]["marksAwarded"] == 10.0
    assert after_att_data["answers"][0]["isCorrect"] == "FULLY_CORRECT"

    # B) Student exam history now reveals score and percentage
    after_hist_resp = await student_client.get(f"/api/v1/students/{student_id}/exams")
    assert after_hist_resp.status_code == 200
    after_hist_items = after_hist_resp.json()
    assert after_hist_items[0]["isResultsReleased"] is True
    assert after_hist_items[0]["marksObtained"] == 10.0
    assert after_hist_items[0]["percentage"] == 100.0

    # C) Exam questions reveal solutions and explanations
    after_exam_resp = await student_client.get(f"/api/v1/exams/{exam_id}")
    assert after_exam_resp.status_code == 200
    after_exam_data = after_exam_resp.json()
    q_data = after_exam_data["questions"][0]
    assert q_data["explanation"] == "Paris is the capital of France."
    correct_options = [o for o in q_data["options"] if o["isCorrect"]]
    assert len(correct_options) == 1
    assert correct_options[0]["text"] == "Paris"


@pytest.mark.asyncio
async def test_result_redaction_incorrect_mcq_before_and_after_release(
    auth_client_factory, db_session: AsyncSession
):
    """Verify that an incorrect MCQ answer (with penalty / 0 marks) is properly redacted before release:

    1. DB stores actual penalty / zero marks and isCorrect = INCORRECT.
    2. HTTP response to student hides marksObtained, marksAwarded, isCorrect, feedback, gradingStatus.
    3. Once results are released, actual marks and correctness become visible.
    """
    school = await create_school_factory(db_session, school_code="REDACT-FAIL-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.redactfail@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        max_marks=10,
        is_published=True,
        is_results_released=False,
        negative_marking=True,
        negative_marks=1.0,
    )

    q1 = await create_question_factory(
        db_session,
        exam=exam,
        question_type=QuestionType.MULTIPLE_CHOICE,
        marks=4.0,
        text="What is 2 + 2?",
        explanation="2 + 2 = 4.",
        options_data=[
            {"text": "4", "isCorrect": True},
            {"text": "5", "isCorrect": False},
        ],
    )
    from app.core.models import QuestionOption

    opts_res = await db_session.execute(
        select(QuestionOption).where(QuestionOption.questionId == q1.id)
    )
    all_opts = opts_res.scalars().all()
    wrong_opt = [opt for opt in all_opts if not opt.isCorrect][0]

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.redactfail@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )

    attempt = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student,
        status=StudentExamStatus.IN_PROGRESS,
    )
    db_answer = await create_attempt_answer_factory(
        db_session,
        attempt=attempt,
        question=q1,
    )
    await db_session.commit()

    student_client = await auth_client_factory(student_user)
    teacher_client = await auth_client_factory(teacher_user)

    attempt_id = str(attempt.id)
    student_id = str(student.id)
    exam_id = str(exam.id)

    # 1. Student submits WRONG option
    submit_payload = {
        "id": attempt_id,
        "answers": [
            {
                "id": str(db_answer.id),
                "textAnswer": None,
                "selectedOptions": [{"optionId": str(wrong_opt.id)}],
            }
        ],
    }
    submit_resp = await student_client.post("/api/v1/attempts/submit", json=submit_payload)
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()

    # Redacted in submit response
    assert submit_data["marksObtained"] is None
    assert submit_data["answers"][0]["marksAwarded"] is None
    assert submit_data["answers"][0]["isCorrect"] is None
    assert submit_data["answers"][0]["feedback"] is None
    assert submit_data["answers"][0]["gradingStatus"] is None

    # 2. Check DB directly: contains internal penalty / incorrect status
    from tests.conftest import TestAsyncSessionLocal

    stmt = (
        select(StudentExam)
        .where(StudentExam.id == attempt_id)
        .options(
            selectinload(StudentExam.answers).selectinload(StudentExamAnswer.selectedOptions)
        )
    )
    async with TestAsyncSessionLocal() as verify_session:
        db_exam_res = (await verify_session.execute(stmt)).scalar_one()
        assert db_exam_res.answers[0].isCorrect == Correctness.INCORRECT
        # Penalty applied: marksAwarded is negative (-1.0)
        assert db_exam_res.answers[0].marksAwarded == -1.0

    # 3. GET attempt before release: all values hidden
    get_attempt_resp = await student_client.get(f"/api/v1/attempts/{attempt_id}")
    assert get_attempt_resp.status_code == 200
    att_data = get_attempt_resp.json()
    assert att_data["marksObtained"] is None
    assert att_data["answers"][0]["marksAwarded"] is None
    assert att_data["answers"][0]["isCorrect"] is None
    assert att_data["answers"][0]["feedback"] is None
    assert att_data["answers"][0]["gradingStatus"] is None

    # 4. GET student exams history before release: score and percentage hidden
    hist_resp = await student_client.get(f"/api/v1/students/{student_id}/exams")
    assert hist_resp.status_code == 200
    hist_items = hist_resp.json()
    assert hist_items[0]["marksObtained"] is None
    assert hist_items[0]["percentage"] is None

    # 5. Teacher releases results
    rel_resp = await teacher_client.post(f"/api/v1/exams/{exam_id}/release-results")
    assert rel_resp.status_code == 200

    # 6. After release: student sees actual score and INCORRECT flag
    after_att_resp = await student_client.get(f"/api/v1/attempts/{attempt_id}")
    assert after_att_resp.status_code == 200
    after_data = after_att_resp.json()
    assert after_data["marksObtained"] is not None
    assert after_data["answers"][0]["marksAwarded"] == -1.0
    assert after_data["answers"][0]["isCorrect"] == "INCORRECT"
    assert after_data["answers"][0]["gradingStatus"] is not None

