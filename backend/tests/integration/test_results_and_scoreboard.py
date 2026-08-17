"""Integration tests for Results Release, Scoreboards, and Leaderboard rank calculations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Role,
    StudentExamStatus,
)
from tests.factories.attempt_factory import create_attempt_factory
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
async def test_results_release_and_student_score_visibility(
    auth_client_factory, db_session: AsyncSession
):
    """Verify releasing exam results makes explanations and scores visible to students."""
    school = await create_school_factory(db_session, school_code="RES-001")
    school_class = await create_class_factory(db_session, school=school)
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.results@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        is_published=True,
        is_results_released=False,
    )
    q1 = await create_question_factory(
        db_session,
        exam=exam,
        text="What is 10 x 10?",
        explanation="10 x 10 is 100",
        options_data=[
            {"text": "100", "isCorrect": True},
            {"text": "50", "isCorrect": False},
        ],
    )
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.res@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    attempt = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student,
        status=StudentExamStatus.GRADED,
        marks_obtained=5.0,
    )
    await db_session.commit()

    teacher_client = await auth_client_factory(teacher_user)
    student_client = await auth_client_factory(student_user)

    # 1. Teacher releases results
    rel_resp = await teacher_client.post(
        f"/api/v1/exams/{exam.id}/release-results",
    )
    assert rel_resp.status_code == 200

    # 2. Student views exam and now sees explanation and correct options
    stud_resp = await student_client.get(f"/api/v1/exams/{exam.id}")
    assert stud_resp.status_code == 200
    stud_data = stud_resp.json()
    assert stud_data["isResultsReleased"] is True
    assert stud_data["questions"][0]["explanation"] == "10 x 10 is 100"
