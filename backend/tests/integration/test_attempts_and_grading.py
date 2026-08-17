"""Integration tests for exam attempts, answer submission, timer deadline enforcement, and auto-grading."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    QuestionType,
    Role,
    StudentExam,
    StudentExamStatus,
)
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import (
    create_exam_factory,
    create_question_factory,
)
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_attempt_submission_and_mcq_msq_grading(
    auth_client_factory, db_session: AsyncSession
):
    """Verify student can start attempt, submit answers for MCQ/MSQ, and receive accurate auto-grading."""
    # 1. Setup School, Class, Teacher, and Exam
    school = await create_school_factory(db_session, school_code="ATT-001")
    school_class = await create_class_factory(db_session, school=school)
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.att@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        negative_marking=True,
        negative_marks=1.0,
        is_published=True,
        is_public=True,
    )

    # Question 1: MCQ (5 marks)
    q1 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=1,
        text="What is the capital of France?",
        marks=5,
        question_type=QuestionType.MULTIPLE_CHOICE,
        options_data=[
            {"text": "Paris", "isCorrect": True},
            {"text": "London", "isCorrect": False},
        ],
    )
    # Question 2: MSQ (4 marks, 2 correct options)
    q2 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=2,
        text="Select prime numbers",
        marks=4,
        question_type=QuestionType.MULTIPLE_SELECT,
        options_data=[
            {"text": "2", "isCorrect": True},
            {"text": "3", "isCorrect": True},
            {"text": "4", "isCorrect": False},
        ],
    )

    # 2. Setup Student enrolled in the same school and class
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.attempt@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    # Re-fetch questions to load options
    await db_session.refresh(q1)
    await db_session.refresh(q2)

    student_client = await auth_client_factory(student_user)

    # 3. Start Exam Attempt
    start_resp = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam.id},
    )
    assert start_resp.status_code in (200, 201)
    attempt_data = start_resp.json()
    attempt_id = attempt_data["id"]
    answers_shells = attempt_data["answers"]
    ans1_shell = next(a for a in answers_shells if a["questionId"] == q1.id)
    ans2_shell = next(a for a in answers_shells if a["questionId"] == q2.id)

    from app.core.models import QuestionOption

    res1 = await db_session.execute(
        select(QuestionOption).where(QuestionOption.questionId == q1.id)
    )
    q1_opts = res1.scalars().all()
    paris_opt = next(o for o in q1_opts if o.text == "Paris")

    res2 = await db_session.execute(
        select(QuestionOption).where(QuestionOption.questionId == q2.id)
    )
    q2_opts = res2.scalars().all()
    p2_opt = next(o for o in q2_opts if o.text == "2")
    p3_opt = next(o for o in q2_opts if o.text == "3")

    # 4. Submit Attempt with Answers
    submit_payload = {
        "id": attempt_id,
        "answers": [
            {
                "id": ans1_shell["id"],
                "selectedOptions": [{"optionId": paris_opt.id}],
            },
            {
                "id": ans2_shell["id"],
                "selectedOptions": [
                    {"optionId": p2_opt.id},
                    {"optionId": p3_opt.id},
                ],
            },
        ],
    }
    submit_resp = await student_client.post(
        "/api/v1/attempts/submit", json=submit_payload
    )
    assert submit_resp.status_code == 200

    # 5. Verify in Database
    result = await db_session.execute(
        select(StudentExam).where(StudentExam.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    assert attempt is not None
    assert attempt.status in (StudentExamStatus.SUBMITTED, StudentExamStatus.GRADED)
    assert attempt.marksObtained == 9.0  # 5 + 4


@pytest.mark.asyncio
async def test_deadline_expired_attempt_enforcement(
    auth_client_factory, db_session: AsyncSession
):
    """Verify submitting answers after deadline + grace period is rejected."""
    school = await create_school_factory(db_session, school_code="EXP-001")
    school_class = await create_class_factory(db_session, school=school)
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.late@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        duration=10,  # 10 minutes
        is_published=True,
    )
    q1 = await create_question_factory(db_session, exam=exam)
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.late@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    student_client = await auth_client_factory(student_user)

    # 1. Start Exam Attempt
    start_resp = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam.id},
    )
    assert start_resp.status_code in (200, 201)
    attempt_data = start_resp.json()
    attempt_id = attempt_data["id"]
    ans_shell_id = attempt_data["answers"][0]["id"]

    # 2. Artificially backdate startedAt in DB by 30 minutes
    result = await db_session.execute(
        select(StudentExam).where(StudentExam.id == attempt_id)
    )
    attempt = result.scalar_one()
    attempt.startedAt = datetime.now(UTC) - timedelta(minutes=30)
    await db_session.commit()

    # 3. Submitting expired attempt should return 400 Bad Request
    submit_payload = {
        "id": attempt_id,
        "answers": [
            {
                "id": ans_shell_id,
                "textAnswer": "Late Answer",
            }
        ],
    }
    submit_resp = await student_client.post(
        "/api/v1/attempts/submit", json=submit_payload
    )
    assert submit_resp.status_code == 400
    assert (
        "time" in submit_resp.json()["detail"].lower()
        or "expired" in submit_resp.json()["detail"].lower()
    )
