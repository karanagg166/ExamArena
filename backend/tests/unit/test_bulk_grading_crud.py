"""Unit tests for bulk grading CRUD query functions and summary computations."""

import pytest

from app.core.models import (
    GradingStatus,
    QuestionType,
    Role,
    StudentExamStatus,
)
from app.grading import crud
from tests.factories.attempt_factory import (
    create_attempt_answer_factory,
    create_attempt_factory,
)
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import (
    create_exam_factory,
    create_question_factory,
    create_section_factory,
)
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.fixture
async def crud_setup(db_session):
    principal = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="crud_p@school.local"
    )
    school = await create_school_factory(
        db_session, creator_user=principal, school_code="SCH-CRUD-1"
    )
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="crud_t@school.local"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    section = await create_section_factory(db_session, exam=exam)

    q_mcq = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=1,
        question_type=QuestionType.MULTIPLE_CHOICE,
        marks=2,
    )
    q_sa = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=2,
        question_type=QuestionType.SHORT_ANSWER,
        marks=5,
    )
    q_essay = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=3,
        question_type=QuestionType.ESSAY,
        marks=10,
    )

    school_class = await create_class_factory(db_session, school=school)
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="crud_s@school.local"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    attempt = await create_attempt_factory(
        db_session, exam=exam, student=student, status=StudentExamStatus.SUBMITTED
    )

    await db_session.commit()

    return {
        "exam": exam,
        "attempt": attempt,
        "q_mcq": q_mcq,
        "q_sa": q_sa,
        "q_essay": q_essay,
    }


@pytest.mark.asyncio
async def test_get_exam_grading_summary_empty(db_session, crud_setup):
    """When no answers exist or only objective answers exist, subjective summary returns zeroes."""
    exam = crud_setup["exam"]
    summary = await crud.get_exam_grading_summary(exam.id, db_session)
    assert summary == {
        "totalSubjectiveAnswers": 0,
        "pending": 0,
        "aiSuggestionsReady": 0,
        "teacherGraded": 0,
    }


@pytest.mark.asyncio
async def test_get_exam_grading_summary_breakdown(db_session, crud_setup):
    """Accurately calculates total, pending, aiSuggestionsReady, and teacherGraded."""
    exam = crud_setup["exam"]
    att = crud_setup["attempt"]
    q_mcq = crud_setup["q_mcq"]
    q_sa = crud_setup["q_sa"]
    q_essay = crud_setup["q_essay"]

    # 1. Objective MCQ -> ignored
    await create_attempt_answer_factory(
        db_session, attempt=att, question=q_mcq, marks_awarded=2.0, grading_status=GradingStatus.AUTO_GRADED
    )
    # 2. Pending short answer
    await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Answer pending", grading_status=GradingStatus.PENDING
    )
    # 3. AI draft ready essay
    essay_ans = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_essay, text_answer="Essay with proposal", grading_status=GradingStatus.PENDING
    )
    essay_ans.aiSuggestedMarks = 8.0

    await db_session.commit()

    summary = await crud.get_exam_grading_summary(exam.id, db_session)
    assert summary["totalSubjectiveAnswers"] == 2
    assert summary["pending"] == 1
    assert summary["aiSuggestionsReady"] == 1
    assert summary["teacherGraded"] == 0


@pytest.mark.asyncio
async def test_count_eligible_subjective_answers_filters_proposals(db_session, crud_setup):
    """Verifies count_eligible_subjective_answers respects regenerate_existing flag."""
    exam = crud_setup["exam"]
    att = crud_setup["attempt"]
    q_sa = crud_setup["q_sa"]

    ans = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Student answer", grading_status=GradingStatus.PENDING
    )
    ans.aiSuggestedMarks = 4.0
    await db_session.commit()

    # regenerate_existing = False -> 0 eligible
    count_default = await crud.count_eligible_subjective_answers(exam.id, False, db_session)
    assert count_default == 0

    # regenerate_existing = True -> 1 eligible
    count_regen = await crud.count_eligible_subjective_answers(exam.id, True, db_session)
    assert count_regen == 1


@pytest.mark.asyncio
async def test_get_pending_subjective_answers_for_exam_limit(db_session, crud_setup):
    """Bounded batch query respects limit parameter and eagerly loads question and exam."""
    exam = crud_setup["exam"]
    att = crud_setup["attempt"]
    q_sa = crud_setup["q_sa"]

    await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Ans 1", grading_status=GradingStatus.PENDING
    )
    await db_session.commit()

    batch = await crud.get_pending_subjective_answers_for_exam(
        exam_id=exam.id,
        regenerate_existing=False,
        limit=10,
        session=db_session,
    )
    assert len(batch) == 1
    assert batch[0].question is not None
    assert batch[0].studentExam.exam is not None
