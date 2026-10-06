"""API integration tests for student subjective answer grading with AI assistance.

Covers:
- Teacher authorization and RBAC (unauthenticated 401, student 403, unauthorized teacher 403)
- Objective question guard (400 for MULTIPLE_CHOICE)
- AI proposal generation (SHORT_ANSWER & ESSAY, non-finalizing proposal, idempotency)
- Deterministic empty answer handling (0 marks, no AI invocation)
- Teacher accept AI proposal (finalizes marks, updates attempt score & status)
- Teacher manual grade override & score validation (bounds check 422)
- Teacher reject AI proposal (clears proposal, leaves answer in pending state)
- Teacher retrieval of answer details (reference answer, rubric, AI proposal)
- Student redaction & non-leakage of AI fields
"""

from unittest.mock import AsyncMock, patch

import pytest

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.schemas.grading import AIGradingResult, GradingConfidence, RubricGrade
from app.attempts.schemas import StudentAnswerResponse
from app.core.models import (
    Correctness,
    GradingStatus,
    QuestionType,
    Role,
    StudentExamAnswer,
    StudentExamStatus,
)
from tests.factories.attempt_factory import (
    create_attempt_answer_factory,
    create_attempt_factory,
)
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
async def grading_setup(db_session):
    """Sets up an exam with teacher, student, subjective question, and attempt."""
    principal_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal_grading@school.local"
    )
    school = await create_school_factory(
        db_session, creator_user=principal_user, school_code="SCH-GRADE-1"
    )

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher_owner@school.local"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(db_session, teacher=teacher)
    section = await create_section_factory(
        db_session, exam=exam, name="Subjective Section", marks_per_question=5
    )

    question = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=1,
        text="Explain photosynthesis and its chemical equation.",
        marks=5,
        question_type=QuestionType.SHORT_ANSWER,
        explanation="Photosynthesis produces glucose and oxygen from carbon dioxide and water.",
    )
    question.referenceAnswer = "Plants convert light energy into chemical energy: 6CO2 + 6H2O -> C6H12O6 + 6O2."
    question.gradingRubric = [
        {"criterion": "Defines process", "marks": 2},
        {"criterion": "Provides chemical equation", "marks": 2},
        {"criterion": "Mentions products/reactants", "marks": 1},
    ]
    await db_session.flush()

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student_grade@school.local"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school
    )

    attempt = await create_attempt_factory(
        db_session,
        exam=exam,
        student=student,
        status=StudentExamStatus.SUBMITTED,
        marks_obtained=0.0,
    )

    answer = await create_attempt_answer_factory(
        db_session,
        attempt=attempt,
        question=question,
        text_answer="Plants use light energy to turn CO2 and water into glucose and oxygen.",
        marks_awarded=0.0,
        is_correct=None,
        grading_status=GradingStatus.PENDING,
    )
    await db_session.commit()

    return {
        "school": school,
        "teacher_user": teacher_user,
        "teacher": teacher,
        "student_user": student_user,
        "student": student,
        "exam": exam,
        "question": question,
        "attempt": attempt,
        "answer": answer,
    }


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_grading(client):
    """Unauthenticated requests must be rejected with 401."""
    ans_id = "ans_any_id"
    res1 = await client.post(f"/api/v1/student-answers/{ans_id}/ai-grade")
    assert res1.status_code == 401

    res2 = await client.post(f"/api/v1/student-answers/{ans_id}/grade/accept-ai")
    assert res2.status_code == 401

    res3 = await client.patch(
        f"/api/v1/student-answers/{ans_id}/grade", json={"marks": 3.0}
    )
    assert res3.status_code == 401

    res4 = await client.post(f"/api/v1/student-answers/{ans_id}/grade/reject-ai")
    assert res4.status_code == 401

    res5 = await client.get(f"/api/v1/student-answers/{ans_id}")
    assert res5.status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_access_grading(auth_client_factory, grading_setup):
    """Students must be denied access with 403 on all grading endpoints."""
    student_client = await auth_client_factory(grading_setup["student_user"])
    ans_id = grading_setup["answer"].id

    res1 = await student_client.post(f"/api/v1/student-answers/{ans_id}/ai-grade")
    assert res1.status_code == 403

    res2 = await student_client.post(f"/api/v1/student-answers/{ans_id}/grade/accept-ai")
    assert res2.status_code == 403

    res3 = await student_client.patch(
        f"/api/v1/student-answers/{ans_id}/grade", json={"marks": 4.0}
    )
    assert res3.status_code == 403

    res4 = await student_client.post(f"/api/v1/student-answers/{ans_id}/grade/reject-ai")
    assert res4.status_code == 403

    res5 = await student_client.get(f"/api/v1/student-answers/{ans_id}")
    assert res5.status_code == 403


@pytest.mark.asyncio
async def test_unauthorized_teacher_cannot_grade_other_teachers_exam(
    auth_client_factory, db_session, grading_setup
):
    """Teachers from another school/not owning the exam must receive 403."""
    other_principal = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="other_p@school2.local"
    )
    other_school = await create_school_factory(
        db_session, creator_user=other_principal, school_code="SCH-OTHER-2"
    )
    other_teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="other_t@school2.local"
    )
    await create_teacher_factory(db_session, user=other_teacher_user, school=other_school)
    await db_session.commit()

    other_client = await auth_client_factory(other_teacher_user)
    ans_id = grading_setup["answer"].id

    res = await other_client.post(f"/api/v1/student-answers/{ans_id}/ai-grade")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_ai_grade_objective_question_rejected_with_400(
    auth_client_factory, db_session, grading_setup
):
    """AI grading must refuse objective questions (e.g. MULTIPLE_CHOICE) with 400 Bad Request."""
    mcq_question = await create_question_factory(
        db_session,
        exam=grading_setup["exam"],
        question_number=2,
        text="What is the capital of France?",
        marks=2,
        question_type=QuestionType.MULTIPLE_CHOICE,
    )
    mcq_answer = await create_attempt_answer_factory(
        db_session,
        attempt=grading_setup["attempt"],
        question=mcq_question,
        marks_awarded=2.0,
        is_correct=Correctness.FULLY_CORRECT,
        grading_status=GradingStatus.AUTO_GRADED,
    )
    await db_session.commit()

    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    res = await teacher_client.post(f"/api/v1/student-answers/{mcq_answer.id}/ai-grade")
    assert res.status_code == 400
    assert "SHORT_ANSWER and ESSAY" in res.json()["detail"]


@pytest.mark.asyncio
async def test_ai_grade_short_answer_proposes_score_without_finalizing(
    auth_client_factory, db_session, grading_setup
):
    """AI grading creates a proposal draft but does NOT finalize student marks or change attempt status."""
    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    ans = grading_setup["answer"]

    mock_result = AIGradingResult(
        suggested_marks=4.0,
        max_marks=5.0,
        rubric_breakdown=[
            RubricGrade(
                criterion="Defines process",
                max_marks=2.0,
                awarded_marks=2.0,
                justification="Accurately defines photosynthesis.",
            ),
            RubricGrade(
                criterion="Provides chemical equation",
                max_marks=2.0,
                awarded_marks=1.0,
                justification="Mentioned reactants but omitted balanced formula.",
            ),
            RubricGrade(
                criterion="Mentions products/reactants",
                max_marks=1.0,
                awarded_marks=1.0,
                justification="Correctly identifies CO2, water, glucose, oxygen.",
            ),
        ],
        feedback="Good explanation of photosynthesis; includes reactants and products clearly.",
        confidence=GradingConfidence.HIGH,
        warnings=[],
    )

    with patch(
        "app.ai.grading.service.CohereClient.extract_structured_json",
        new_callable=AsyncMock,
        return_value=(mock_result.model_dump_json(), {}),
    ):
        res = await teacher_client.post(f"/api/v1/student-answers/{ans.id}/ai-grade")

    assert res.status_code == 200
    data = res.json()
    assert data["answerId"] == ans.id
    assert data["suggestedMarks"] == 4.0
    assert data["maxMarks"] == 5.0
    assert data["confidence"] == "HIGH"
    assert len(data["rubricBreakdown"]) == 3
    assert data["feedback"] == "Good explanation of photosynthesis; includes reactants and products clearly."

    # Verify DB: AI proposal is saved, BUT marksAwarded is NOT finalized and gradingStatus is still PENDING
    await db_session.refresh(ans)
    assert ans.aiSuggestedMarks == 4.0
    assert ans.aiConfidence == "HIGH"
    assert ans.aiFeedback == data["feedback"]
    assert len(ans.aiGradingBreakdown) == 3
    assert ans.marksAwarded == 0.0  # Still 0.0 / unawarded
    assert ans.gradingStatus == GradingStatus.PENDING  # Still PENDING!
    assert ans.gradedBy is None

    # Attempt score must remain unchanged
    await db_session.refresh(grading_setup["attempt"])
    assert grading_setup["attempt"].marksObtained == 0.0
    assert grading_setup["attempt"].status == StudentExamStatus.SUBMITTED


@pytest.mark.asyncio
async def test_ai_grade_empty_student_answer_deterministic_zero(
    auth_client_factory, db_session, grading_setup
):
    """Empty or whitespace answers must deterministically receive 0 marks without invoking Cohere."""
    ans = grading_setup["answer"]
    ans.textAnswer = "   "
    await db_session.commit()

    teacher_client = await auth_client_factory(grading_setup["teacher_user"])

    with patch(
        "app.ai.grading.service.CohereClient.extract_structured_json",
        new_callable=AsyncMock,
    ) as mock_cohere:
        res = await teacher_client.post(f"/api/v1/student-answers/{ans.id}/ai-grade")

    assert res.status_code == 200
    mock_cohere.assert_not_called()

    data = res.json()
    assert data["suggestedMarks"] == 0.0
    assert data["confidence"] == "HIGH"
    assert data["feedback"] == "No answer provided."


@pytest.mark.asyncio
async def test_ai_grade_idempotency_overwrites_proposal(
    auth_client_factory, db_session, grading_setup
):
    """Running AI grading multiple times safely overwrites previous proposal draft."""
    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    ans = grading_setup["answer"]

    result1 = AIGradingResult(
        suggested_marks=2.0,
        max_marks=5.0,
        rubric_breakdown=[
            RubricGrade(criterion="Criterion 1", max_marks=5.0, awarded_marks=2.0, justification="Partial")
        ],
        feedback="V1 feedback",
        confidence=GradingConfidence.MEDIUM,
        warnings=[],
    )
    result2 = AIGradingResult(
        suggested_marks=4.5,
        max_marks=5.0,
        rubric_breakdown=[
            RubricGrade(criterion="Criterion 1", max_marks=5.0, awarded_marks=4.5, justification="Almost full")
        ],
        feedback="V2 feedback",
        confidence=GradingConfidence.HIGH,
        warnings=[],
    )

    with patch("app.ai.grading.service.CohereClient.extract_structured_json", new_callable=AsyncMock) as mock_cohere:
        mock_cohere.return_value = (result1.model_dump_json(), {})
        res1 = await teacher_client.post(f"/api/v1/student-answers/{ans.id}/ai-grade")
        assert res1.status_code == 200
        assert res1.json()["suggestedMarks"] == 2.0

        mock_cohere.return_value = (result2.model_dump_json(), {})
        res2 = await teacher_client.post(f"/api/v1/student-answers/{ans.id}/ai-grade")
        assert res2.status_code == 200
        assert res2.json()["suggestedMarks"] == 4.5

    await db_session.refresh(ans)
    assert ans.aiSuggestedMarks == 4.5
    assert ans.aiFeedback == "V2 feedback"


@pytest.mark.asyncio
async def test_accept_ai_proposal_finalizes_marks_and_recalculates_attempt(
    auth_client_factory, db_session, grading_setup
):
    """Accepting AI suggestion sets marksAwarded, teacher user id, MANUALLY_GRADED, and recalculates attempt."""
    ans = grading_setup["answer"]
    ans.aiSuggestedMarks = 4.0
    ans.aiConfidence = "HIGH"
    ans.aiFeedback = "Good work on photosynthesis."
    ans.aiGradingBreakdown = [{"criterion": "Defines process", "max_marks": 5.0, "awarded_marks": 4.0, "justification": "Good"}]
    ans.aiWarnings = []
    await db_session.commit()

    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    res = await teacher_client.post(f"/api/v1/student-answers/{ans.id}/grade/accept-ai")

    assert res.status_code == 200
    data = res.json()
    assert data["answerId"] == ans.id
    assert data["marksAwarded"] == 4.0
    assert data["maxMarks"] == 5.0
    assert data["feedback"] == "Good work on photosynthesis."
    assert data["gradingStatus"] == "MANUALLY_GRADED"
    assert data["gradedBy"] == grading_setup["teacher_user"].id
    assert data["isCorrect"] == "PARTIALLY_CORRECT"

    # Verify DB state
    await db_session.refresh(ans)
    assert ans.marksAwarded == 4.0
    assert ans.gradingStatus == GradingStatus.MANUALLY_GRADED
    assert ans.gradedBy == grading_setup["teacher_user"].id
    assert ans.gradedAt is not None

    # Check attempt marks recalculated and status updated to GRADED
    attempt = grading_setup["attempt"]
    await db_session.refresh(attempt)
    assert attempt.marksObtained == 4.0
    assert attempt.status == StudentExamStatus.GRADED


@pytest.mark.asyncio
async def test_accept_ai_proposal_without_prior_proposal_fails_400(
    auth_client_factory, grading_setup
):
    """Calling accept-ai without an existing AI suggestion returns 400 Bad Request."""
    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    ans_id = grading_setup["answer"].id

    res = await teacher_client.post(f"/api/v1/student-answers/{ans_id}/grade/accept-ai")
    assert res.status_code == 400
    assert "No AI grading proposal available" in res.json()["detail"]


@pytest.mark.asyncio
async def test_teacher_manual_grade_override(
    auth_client_factory, db_session, grading_setup
):
    """Teacher can manually override marks and feedback."""
    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    ans = grading_setup["answer"]

    res = await teacher_client.patch(
        f"/api/v1/student-answers/{ans.id}/grade",
        json={"marks": 4.5, "feedback": "Teacher override: very close to full marks."},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["marksAwarded"] == 4.5
    assert data["feedback"] == "Teacher override: very close to full marks."
    assert data["gradingStatus"] == "MANUALLY_GRADED"
    assert data["gradedBy"] == grading_setup["teacher_user"].id

    await db_session.refresh(ans)
    assert ans.marksAwarded == 4.5
    assert ans.feedback == "Teacher override: very close to full marks."

    attempt = grading_setup["attempt"]
    await db_session.refresh(attempt)
    assert attempt.marksObtained == 4.5
    assert attempt.status == StudentExamStatus.GRADED


@pytest.mark.asyncio
async def test_teacher_manual_grade_invalid_score_bounds_rejected_422(
    auth_client_factory, grading_setup
):
    """Negative marks and marks exceeding maximum question marks return 422 Unprocessable Entity."""
    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    ans_id = grading_setup["answer"].id

    # Negative marks rejected by schema or router
    res_neg = await teacher_client.patch(
        f"/api/v1/student-answers/{ans_id}/grade",
        json={"marks": -2.0, "feedback": "Negative score"},
    )
    assert res_neg.status_code == 422

    # Marks exceeding maxMarks (5) rejected
    res_high = await teacher_client.patch(
        f"/api/v1/student-answers/{ans_id}/grade",
        json={"marks": 9.0, "feedback": "Too high"},
    )
    assert res_high.status_code == 422
    assert "Marks must be between 0 and 5.0" in res_high.json()["detail"]


@pytest.mark.asyncio
async def test_teacher_reject_ai_proposal(
    auth_client_factory, db_session, grading_setup
):
    """Rejecting an AI proposal clears the proposal draft and leaves the answer ready for manual grading."""
    ans = grading_setup["answer"]
    ans.aiSuggestedMarks = 3.0
    ans.aiConfidence = "LOW"
    ans.aiFeedback = "Initial AI guess"
    ans.aiGradingBreakdown = [{"criterion": "Concept", "max_marks": 5.0, "awarded_marks": 3.0, "justification": "Ok"}]
    ans.aiWarnings = ["Low confidence"]
    await db_session.commit()

    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    res = await teacher_client.post(f"/api/v1/student-answers/{ans.id}/grade/reject-ai")

    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"

    await db_session.refresh(ans)
    assert ans.aiSuggestedMarks is None
    assert ans.aiConfidence is None
    assert ans.aiFeedback is None
    assert ans.aiGradingBreakdown is None
    assert ans.aiWarnings is None
    # Still pending manual grade
    assert ans.gradingStatus == GradingStatus.PENDING


@pytest.mark.asyncio
async def test_teacher_get_answer_details(
    auth_client_factory, db_session, grading_setup
):
    """Teacher can retrieve full answer details including reference solutions and AI proposal."""
    ans = grading_setup["answer"]
    ans.aiSuggestedMarks = 4.0
    ans.aiConfidence = "HIGH"
    ans.aiFeedback = "Structured feedback"
    ans.aiGradingBreakdown = [
        {"criterion": "Defines process", "max_marks": 2.0, "awarded_marks": 2.0, "justification": "Good"}
    ]
    await db_session.commit()

    teacher_client = await auth_client_factory(grading_setup["teacher_user"])
    res = await teacher_client.get(f"/api/v1/student-answers/{ans.id}")

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == ans.id
    assert data["questionType"] == "SHORT_ANSWER"
    assert "photosynthesis" in data["questionText"]
    assert data["referenceAnswer"] is not None
    assert len(data["gradingRubric"]) == 3
    assert data["aiProposal"] is not None
    assert data["aiProposal"]["suggestedMarks"] == 4.0
    assert data["aiProposal"]["rubricBreakdown"][0]["criterion"] == "Defines process"


@pytest.mark.asyncio
async def test_student_response_never_leaks_ai_proposal(db_session, grading_setup):
    """Ensure student-facing serialization never leaks AI proposal draft fields."""
    ans = grading_setup["answer"]
    ans.aiSuggestedMarks = 4.0
    ans.aiConfidence = "HIGH"
    ans.aiFeedback = "Teacher-only AI evaluation"
    ans.aiGradingBreakdown = [{"criterion": "Process", "max_marks": 5.0, "awarded_marks": 4.0, "justification": "Ok"}]
    ans.aiWarnings = ["AI warning"]
    await db_session.commit()
    await db_session.refresh(ans)

    stmt = (
        select(StudentExamAnswer)
        .where(StudentExamAnswer.id == ans.id)
        .options(selectinload(StudentExamAnswer.selectedOptions))
    )
    ans_loaded = (await db_session.execute(stmt)).scalar_one()

    student_dto = StudentAnswerResponse.model_validate(ans_loaded)
    dumped = student_dto.model_dump()

    assert "aiSuggestedMarks" not in dumped
    assert "aiConfidence" not in dumped
    assert "aiFeedback" not in dumped
    assert "aiGradingBreakdown" not in dumped
    assert "aiWarnings" not in dumped
    assert "aiGradedAt" not in dumped
    assert "gradedBy" not in dumped
