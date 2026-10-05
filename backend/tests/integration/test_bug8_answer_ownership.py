"""Integration tests for Bug 8: Option, Question, and Attempt answer ownership integrity.

Invariants verified:
1. Submitting an option belonging to Question B for Question A fails with HTTP 400.
2. Submitting an unknown answer ID not belonging to the attempt fails with HTTP 400.
3. Submitting duplicate answer IDs in one submission fails with HTTP 422.
4. Submitting duplicate option IDs for the same answer fails with HTTP 422.
5. Submitting valid options matching their corresponding questions succeeds with HTTP 200.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import QuestionOption, QuestionType, Role, StudentExamStatus
from tests.factories.attempt_factory import create_attempt_factory, create_attempt_answer_factory
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory, create_question_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_answer_and_option_ownership_integrity(
    auth_client_factory, db_session: AsyncSession
):
    school = await create_school_factory(db_session, school_code="OWN-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.own@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        is_published=True,
    )

    # Question A
    q_a = await create_question_factory(
        db_session,
        exam=exam,
        question_number=1,
        question_type=QuestionType.MULTIPLE_CHOICE,
        text="Question A",
        options_data=[
            {"text": "Option A1", "isCorrect": True},
            {"text": "Option A2", "isCorrect": False},
        ],
    )
    # Question B
    q_b = await create_question_factory(
        db_session,
        exam=exam,
        question_number=2,
        question_type=QuestionType.MULTIPLE_CHOICE,
        text="Question B",
        options_data=[
            {"text": "Option B1", "isCorrect": True},
            {"text": "Option B2", "isCorrect": False},
        ],
    )

    opts_a = (
        (await db_session.execute(select(QuestionOption).where(QuestionOption.questionId == q_a.id)))
        .scalars()
        .all()
    )
    opts_b = (
        (await db_session.execute(select(QuestionOption).where(QuestionOption.questionId == q_b.id)))
        .scalars()
        .all()
    )

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.own@test.examarena.dev"
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
    ans_a = await create_attempt_answer_factory(
        db_session,
        attempt=attempt,
        question=q_a,
    )
    ans_b = await create_attempt_answer_factory(
        db_session,
        attempt=attempt,
        question=q_b,
    )
    await db_session.commit()

    attempt_id = str(attempt.id)
    ans_a_id = str(ans_a.id)
    ans_b_id = str(ans_b.id)
    opt_a1_id = str(opts_a[0].id)
    opt_b1_id = str(opts_b[0].id)

    student_client = await auth_client_factory(student_user)

    # 1. Option from Question B submitted for Question A -> 400
    resp_cross_option = await student_client.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_id,
            "answers": [
                {
                    "id": ans_a_id,
                    "textAnswer": None,
                    "selectedOptions": [{"optionId": opt_b1_id}],  # Option from Question B!
                }
            ],
        },
    )
    assert resp_cross_option.status_code == 400
    assert "belong" in resp_cross_option.json()["detail"].lower()

    # 2. Unknown answer ID not belonging to attempt -> 400
    resp_unknown_ans = await student_client.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_id,
            "answers": [
                {
                    "id": "unknown-answer-shell-id",
                    "textAnswer": None,
                    "selectedOptions": [{"optionId": opt_a1_id}],
                }
            ],
        },
    )
    assert resp_unknown_ans.status_code == 400
    assert "belong" in resp_unknown_ans.json()["detail"].lower()

    # 3. Duplicate answer ID in submission payload -> 422
    resp_dup_ans = await student_client.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_id,
            "answers": [
                {"id": ans_a_id, "textAnswer": "One", "selectedOptions": []},
                {"id": ans_a_id, "textAnswer": "Two", "selectedOptions": []},
            ],
        },
    )
    assert resp_dup_ans.status_code == 422

    # 4. Duplicate option ID within the same answer -> 422
    resp_dup_opt = await student_client.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_id,
            "answers": [
                {
                    "id": ans_a_id,
                    "textAnswer": None,
                    "selectedOptions": [{"optionId": opt_a1_id}, {"optionId": opt_a1_id}],
                }
            ],
        },
    )
    assert resp_dup_opt.status_code == 422

    # 5. Legitimate options matching their questions -> 200
    resp_valid = await student_client.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_id,
            "answers": [
                {
                    "id": ans_a_id,
                    "textAnswer": None,
                    "selectedOptions": [{"optionId": opt_a1_id}],
                },
                {
                    "id": ans_b_id,
                    "textAnswer": None,
                    "selectedOptions": [{"optionId": opt_b1_id}],
                },
            ],
        },
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["status"] in ("SUBMITTED", "GRADED")


@pytest.mark.asyncio
async def test_cross_attempt_answer_shell_idor_protection(
    auth_client_factory, db_session: AsyncSession
):
    """Verify cross-attempt answer IDOR injection is rejected and does not mutate another attempt:

    Student A Attempt A
    Student B Attempt B
    Student A submits Attempt A but supplies Answer Shell ID belonging to Attempt B.
    Expected: HTTP 400 Bad Request.
    DB Verification:
    - Attempt B answer shell remains completely untouched (no answers/options attached).
    - Attempt B remains IN_PROGRESS.
    - Attempt A remains IN_PROGRESS.
    """
    from sqlalchemy.orm import selectinload
    from app.core.models import StudentExam, StudentExamAnswer
    from tests.conftest import TestAsyncSessionLocal

    school = await create_school_factory(db_session, school_code="IDOR-SHELL-01")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.idor@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        is_published=True,
    )
    q1 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=1,
        question_type=QuestionType.MULTIPLE_CHOICE,
        text="Question 1",
        options_data=[
            {"text": "Option 1", "isCorrect": True},
            {"text": "Option 2", "isCorrect": False},
        ],
    )
    opts = (
        (await db_session.execute(select(QuestionOption).where(QuestionOption.questionId == q1.id)))
        .scalars()
        .all()
    )
    opt_1_id = str(opts[0].id)

    # Student A & Attempt A
    user_a = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.a.idor@test.examarena.dev"
    )
    student_a = await create_student_factory(
        db_session, user=user_a, school=school, school_class=school_class
    )
    attempt_a = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student_a,
        status=StudentExamStatus.IN_PROGRESS,
    )
    ans_a = await create_attempt_answer_factory(
        db_session,
        attempt=attempt_a,
        question=q1,
    )

    # Student B & Attempt B
    user_b = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.b.idor@test.examarena.dev"
    )
    student_b = await create_student_factory(
        db_session, user=user_b, school=school, school_class=school_class
    )
    attempt_b = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student_b,
        status=StudentExamStatus.IN_PROGRESS,
    )
    ans_b = await create_attempt_answer_factory(
        db_session,
        attempt=attempt_b,
        question=q1,
    )
    await db_session.commit()

    attempt_a_id = str(attempt_a.id)
    attempt_b_id = str(attempt_b.id)
    ans_b_id = str(ans_b.id)

    client_a = await auth_client_factory(user_a)

    # Student A attempts to inject Answer Shell B into Attempt A submission
    resp_idor_submit = await client_a.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_a_id,
            "answers": [
                {
                    "id": ans_b_id,  # Answer shell belonging to Attempt B!
                    "textAnswer": "Injected malicious text",
                    "selectedOptions": [{"optionId": opt_1_id}],
                }
            ],
        },
    )
    assert resp_idor_submit.status_code == 400
    assert "belong to this attempt" in resp_idor_submit.json()["detail"].lower()

    # DB Integrity Verification:
    # 1. Attempt B must be completely unmodified
    async with TestAsyncSessionLocal() as verify_session:
        stmt_b = (
            select(StudentExam)
            .where(StudentExam.id == attempt_b_id)
            .options(
                selectinload(StudentExam.answers).selectinload(StudentExamAnswer.selectedOptions)
            )
        )
        db_attempt_b = (await verify_session.execute(stmt_b)).scalar_one()
        assert db_attempt_b.status == StudentExamStatus.IN_PROGRESS
        assert db_attempt_b.answers[0].textAnswer is None
        assert len(db_attempt_b.answers[0].selectedOptions) == 0

        # 2. Attempt A was rejected before commit and remains IN_PROGRESS
        stmt_a = (
            select(StudentExam)
            .where(StudentExam.id == attempt_a_id)
            .options(
                selectinload(StudentExam.answers).selectinload(StudentExamAnswer.selectedOptions)
            )
        )
        db_attempt_a = (await verify_session.execute(stmt_a)).scalar_one()
        assert db_attempt_a.status == StudentExamStatus.IN_PROGRESS
        assert db_attempt_a.answers[0].textAnswer is None
        assert len(db_attempt_a.answers[0].selectedOptions) == 0

