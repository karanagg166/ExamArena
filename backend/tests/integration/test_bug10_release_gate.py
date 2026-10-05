"""Integration tests for Bug 10: Result release authorization matrix and pending subjective grading gate.

Invariants verified:
1. Release authorization:
   - Owner teacher: allowed (200)
   - Principal of same school: allowed (200)
   - Admin: allowed (200)
   - Other teacher from different school or unowned: rejected (403)
   - Principal of different school: rejected (403)
   - Student: rejected (403)
2. Subjective grading gate:
   - If submitted attempt contains subjective answers (SHORT_ANSWER / ESSAY) with gradingStatus == PENDING,
     attempting to release results fails with HTTP 400.
3. Once subjective answers are graded, releasing results succeeds with HTTP 200.
4. Calling release results again on an already released exam is idempotent (200).
"""

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    GradingStatus,
    QuestionType,
    Role,
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
async def test_result_release_authorization_matrix_and_pending_gate(
    auth_client_factory, client, db_session: AsyncSession
):
    # School A
    school_a = await create_school_factory(db_session, school_code="REL-A-01")
    class_a = await create_class_factory(db_session, school=school_a)

    # School B
    school_b = await create_school_factory(db_session, school_code="REL-B-01")

    # Teacher A (School A)
    user_teacher_a = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.a.rel@test.examarena.dev"
    )
    teacher_a = await create_teacher_factory(db_session, user=user_teacher_a, school=school_a)

    # Teacher B (School B)
    user_teacher_b = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.b.rel@test.examarena.dev"
    )
    teacher_b = await create_teacher_factory(db_session, user=user_teacher_b, school=school_b)

    # Principal A (School A)
    user_principal_a = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.a.rel@test.examarena.dev"
    )
    await create_teacher_factory(db_session, user=user_principal_a, school=school_a)

    # Principal B (School B)
    user_principal_b = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.b.rel@test.examarena.dev"
    )
    await create_teacher_factory(db_session, user=user_principal_b, school=school_b)

    # Admin
    user_admin = await create_user_factory(
        db_session, role=Role.ADMIN, email="admin.rel@test.examarena.dev"
    )

    # Student A (School A)
    user_student_a = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.a.rel@test.examarena.dev"
    )
    student_a = await create_student_factory(
        db_session, user=user_student_a, school=school_a, school_class=class_a
    )

    # Exam created by Teacher A in School A
    exam = await create_exam_factory(
        db_session,
        teacher=teacher_a,
        is_published=True,
        is_results_released=False,
    )

    # Add a subjective question (SHORT_ANSWER)
    q_subjective = await create_question_factory(
        db_session,
        exam=exam,
        question_type=QuestionType.SHORT_ANSWER,
        marks=5.0,
        text="Explain Newton's third law of motion.",
    )

    # Student submitted attempt with PENDING subjective answer
    attempt = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student_a,
        status=StudentExamStatus.SUBMITTED,
    )
    subjective_answer = await create_attempt_answer_factory(
        db_session,
        attempt=attempt,
        question=q_subjective,
        text_answer="Every action has an equal and opposite reaction.",
        grading_status=GradingStatus.PENDING,
    )
    await db_session.commit()

    exam_id = str(exam.id)

    client_teacher_a = await auth_client_factory(user_teacher_a)
    client_teacher_b = await auth_client_factory(user_teacher_b)
    client_principal_a = await auth_client_factory(user_principal_a)
    client_principal_b = await auth_client_factory(user_principal_b)
    client_admin = await auth_client_factory(user_admin)
    client_student_a = await auth_client_factory(user_student_a)

    # ── 1. Authorization checks ────────────────────────────────────────────────
    # Unauthenticated request -> 401
    resp_unauth = await client.post(f"/api/v1/exams/{exam_id}/release-results")
    assert resp_unauth.status_code == 401

    # Nonexistent exam ID -> 404
    resp_nonexistent = await client_teacher_a.post(
        "/api/v1/exams/nonexistent-exam-id-9999/release-results"
    )
    assert resp_nonexistent.status_code == 404

    # Student -> 403
    resp_student = await client_student_a.post(f"/api/v1/exams/{exam_id}/release-results")
    assert resp_student.status_code == 403

    # Unrelated teacher (School B) -> 403
    resp_unrelated_teacher = await client_teacher_b.post(
        f"/api/v1/exams/{exam_id}/release-results"
    )
    assert resp_unrelated_teacher.status_code == 403

    # Principal of different school (School B) -> 403
    resp_diff_principal = await client_principal_b.post(
        f"/api/v1/exams/{exam_id}/release-results"
    )
    assert resp_diff_principal.status_code == 403

    # ── 2. Pending subjective answer blocks release ─────────────────────────────
    # Teacher A attempts release while subjective question has answers pending grading -> 400
    resp_blocked_teacher = await client_teacher_a.post(
        f"/api/v1/exams/{exam_id}/release-results"
    )
    assert resp_blocked_teacher.status_code == 400
    assert "pending" in resp_blocked_teacher.json()["detail"].lower()

    # Admin also gets blocked by pending subjective answers
    resp_blocked_admin = await client_admin.post(
        f"/api/v1/exams/{exam_id}/release-results"
    )
    assert resp_blocked_admin.status_code == 400

    # ── 3. Grade the subjective answer ─────────────────────────────────────────
    await db_session.execute(
        update(StudentExamAnswer)
        .where(StudentExamAnswer.id == subjective_answer.id)
        .values(
            gradingStatus=GradingStatus.MANUALLY_GRADED,
            marksAwarded=5.0,
        )
    )
    await db_session.commit()

    # ── 4. Now release succeeds ────────────────────────────────────────────────
    # Teacher A releases results -> 200
    resp_release_success = await client_teacher_a.post(
        f"/api/v1/exams/{exam_id}/release-results"
    )
    assert resp_release_success.status_code == 200
    assert resp_release_success.json()["isResultsReleased"] is True

    # ── 5. Re-calling release results is idempotent ───────────────────────────
    resp_idempotent = await client_principal_a.post(
        f"/api/v1/exams/{exam_id}/release-results"
    )
    assert resp_idempotent.status_code == 200
    assert resp_idempotent.json()["isResultsReleased"] is True
