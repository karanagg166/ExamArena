"""API tests for exam-level grading summary and bulk AI evaluation workflow."""

from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import select

from app.ai.grading.service import (
    AIGradingProviderError,
    AIGradingValidationError,
    GradingContextMissingError,
)
from app.ai.schemas.grading import AIGradingResult, GradingConfidence, RubricGrade
from app.audit.actions import AuditAction
from app.core.models import (
    AuditLog,
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


def _mock_ai_result(suggested_marks: float = 4.0, max_marks: float = 5.0) -> AIGradingResult:
    return AIGradingResult(
        suggested_marks=suggested_marks,
        max_marks=max_marks,
        rubric_breakdown=[
            RubricGrade(
                criterion="Accuracy",
                max_marks=max_marks,
                awarded_marks=suggested_marks,
                justification="Accurate and thorough explanation.",
            )
        ],
        feedback="Well explained.",
        confidence=GradingConfidence.HIGH,
        warnings=[],
    )


@pytest.fixture
async def bulk_setup(db_session):
    """Sets up an exam with multiple questions (MCQ, Short Answer, Essay) and student attempts."""
    principal_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal_bulk@school.local"
    )
    school = await create_school_factory(
        db_session, creator_user=principal_user, school_code="SCH-BULK-1"
    )

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher_bulk_owner@school.local"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(db_session, teacher=teacher, name="Biology Midterm")
    section = await create_section_factory(
        db_session, exam=exam, name="Comprehensive Section", marks_per_question=5
    )

    # 1. Objective question: MCQ
    q_mcq = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=1,
        text="What is the powerhouse of the cell?",
        marks=2,
        question_type=QuestionType.MULTIPLE_CHOICE,
    )

    # 2. Subjective question: Short Answer
    q_sa = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=2,
        text="Explain cellular respiration.",
        marks=5,
        question_type=QuestionType.SHORT_ANSWER,
    )
    q_sa.referenceAnswer = "Cells break down glucose to produce ATP."
    q_sa.gradingRubric = [{"criterion": "Process", "marks": 5}]

    # 3. Subjective question: Essay
    q_essay = await create_question_factory(
        db_session,
        exam=exam,
        section=section,
        question_number=3,
        text="Discuss the impact of climate change on ecosystems.",
        marks=10,
        question_type=QuestionType.ESSAY,
    )
    q_essay.referenceAnswer = (
        "Climate change alters temperature, precipitation, and causes habitat loss."
    )
    q_essay.gradingRubric = [{"criterion": "Depth", "marks": 10}]


    await db_session.flush()

    # Create 3 students with attempts
    school_class = await create_class_factory(db_session, school=school)
    students = []
    attempts = []
    for i in range(1, 4):
        s_user = await create_user_factory(
            db_session, role=Role.STUDENT, email=f"student_bulk_{i}@school.local"
        )
        s = await create_student_factory(
            db_session, user=s_user, school=school, school_class=school_class
        )
        att = await create_attempt_factory(
            db_session,
            exam=exam,
            student=s,
            status=StudentExamStatus.SUBMITTED,
            marks_obtained=0.0,
        )
        students.append(s_user)
        attempts.append(att)

    await db_session.commit()

    return {
        "principal_user": principal_user,
        "school": school,
        "teacher_user": teacher_user,
        "teacher": teacher,
        "exam": exam,
        "q_mcq": q_mcq,
        "q_sa": q_sa,
        "q_essay": q_essay,
        "students": students,
        "attempts": attempts,
    }


# ==============================================================================
# AUTHORIZATION TESTS (Part 25)
# ==============================================================================

@pytest.mark.asyncio
async def test_bulk_grading_authorization(client, auth_client_factory, db_session, bulk_setup):
    """Test 401 unauthenticated, 403 student, 403 unrelated teacher, 200 owner teacher & principal."""
    exam_id = bulk_setup["exam"].id

    # 1. Unauthenticated -> 401
    res1 = await client.get(f"/api/v1/exams/{exam_id}/grading/summary")
    assert res1.status_code == 401
    res2 = await client.post(f"/api/v1/exams/{exam_id}/grading/ai-evaluate-pending", json={})
    assert res2.status_code == 401

    # 2. Student -> 403
    student_client = await auth_client_factory(bulk_setup["students"][0])
    res3 = await student_client.get(f"/api/v1/exams/{exam_id}/grading/summary")
    assert res3.status_code == 403
    res4 = await student_client.post(f"/api/v1/exams/{exam_id}/grading/ai-evaluate-pending", json={})
    assert res4.status_code == 403

    # 3. Unrelated teacher -> 403
    other_principal = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="other_principal@other.local"
    )
    other_school = await create_school_factory(
        db_session, creator_user=other_principal, school_code="SCH-OTHER-BULK"
    )
    other_teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="other_teacher@other.local"
    )
    await create_teacher_factory(db_session, user=other_teacher_user, school=other_school)
    await db_session.commit()

    other_client = await auth_client_factory(other_teacher_user)
    res5 = await other_client.get(f"/api/v1/exams/{exam_id}/grading/summary")
    assert res5.status_code == 403
    res6 = await other_client.post(f"/api/v1/exams/{exam_id}/grading/ai-evaluate-pending", json={})
    assert res6.status_code == 403

    # 4. Authorized owner teacher -> 200
    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])
    res7 = await teacher_client.get(f"/api/v1/exams/{exam_id}/grading/summary")
    assert res7.status_code == 200

    # 5. Principal of same school -> 200
    principal_client = await auth_client_factory(bulk_setup["principal_user"])
    res8 = await principal_client.get(f"/api/v1/exams/{exam_id}/grading/summary")
    assert res8.status_code == 200


# ==============================================================================
# SUMMARY API TESTS (Part 14, 26)
# ==============================================================================

@pytest.mark.asyncio
async def test_exam_grading_summary_counts(auth_client_factory, db_session, bulk_setup):
    """Verifies that summary counts correctly partition pending, AI ready, and teacher graded answers, ignoring objective."""
    exam = bulk_setup["exam"]
    att1, att2, att3 = bulk_setup["attempts"]
    q_mcq, q_sa, q_essay = bulk_setup["q_mcq"], bulk_setup["q_sa"], bulk_setup["q_essay"]

    # 1. Objective MCQ answers (should NOT be counted in subjective summary)
    await create_attempt_answer_factory(
        db_session, attempt=att1, question=q_mcq, text_answer=None, marks_awarded=2.0, grading_status=GradingStatus.AUTO_GRADED
    )
    await create_attempt_answer_factory(
        db_session, attempt=att2, question=q_mcq, text_answer=None, marks_awarded=0.0, grading_status=GradingStatus.AUTO_GRADED
    )

    # 2. Subjective Answer 1: PENDING (no AI proposal, no teacher grade)
    await create_attempt_answer_factory(
        db_session, attempt=att1, question=q_sa, text_answer="Cellular respiration makes energy.", grading_status=GradingStatus.PENDING
    )

    # 3. Subjective Answer 2: AI_SUGGESTION_READY (has AI proposal, no final teacher grade)
    ans2 = await create_attempt_answer_factory(
        db_session, attempt=att2, question=q_sa, text_answer="ATP is generated in mitochondria.", grading_status=GradingStatus.PENDING
    )
    ans2.aiSuggestedMarks = 4.0
    ans2.aiConfidence = "HIGH"

    # 4. Subjective Answer 3: TEACHER_GRADED (teacher graded final marks)
    ans3 = await create_attempt_answer_factory(
        db_session, attempt=att3, question=q_sa, text_answer="Full cycle explanation.", marks_awarded=5.0, grading_status=GradingStatus.MANUALLY_GRADED
    )

    # 5. Subjective Answer 4: PENDING ESSAY
    await create_attempt_answer_factory(
        db_session, attempt=att1, question=q_essay, text_answer="Essay about climate change.", grading_status=GradingStatus.PENDING
    )

    await db_session.commit()

    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])
    res = await teacher_client.get(f"/api/v1/exams/{exam.id}/grading/summary")
    assert res.status_code == 200
    data = res.json()

    # Total subjective answers: 4 (q_sa in att1, att2, att3; q_essay in att1). MCQ excluded!
    assert data["totalSubjectiveAnswers"] == 4
    # Pending: 2 (q_sa in att1, q_essay in att1)
    assert data["pending"] == 2
    # AI suggestions ready: 1 (q_sa in att2)
    assert data["aiSuggestionsReady"] == 1
    # Teacher graded: 1 (q_sa in att3)
    assert data["teacherGraded"] == 1


# ==============================================================================
# BULK ELIGIBILITY & INVARIANT TESTS (Part 2, 12, 13, 22)
# ==============================================================================

@pytest.mark.asyncio
async def test_bulk_eligibility_and_grade_preservation(auth_client_factory, db_session, bulk_setup):
    """Ensures:
    - Only SHORT_ANSWER and ESSAY are processed
    - MCQ is ignored
    - Teacher-graded subjective answers are excluded and never overwritten
    - Generating AI proposals does NOT change StudentExam.status to GRADED
    - Final marksAwarded and gradedBy remain untouched
    """
    exam = bulk_setup["exam"]
    att1, att2 = bulk_setup["attempts"][:2]
    q_mcq, q_sa, q_essay = bulk_setup["q_mcq"], bulk_setup["q_sa"], bulk_setup["q_essay"]

    # MCQ answer
    mcq_ans = await create_attempt_answer_factory(
        db_session, attempt=att1, question=q_mcq, text_answer=None, marks_awarded=2.0, grading_status=GradingStatus.AUTO_GRADED
    )
    # Teacher-graded short answer
    graded_sa = await create_attempt_answer_factory(
        db_session,
        attempt=att1,
        question=q_sa,
        text_answer="Student answer already reviewed by teacher.",
        marks_awarded=4.5,
        grading_status=GradingStatus.MANUALLY_GRADED,
    )
    graded_sa.gradedBy = bulk_setup["teacher_user"].id

    # Pending short answer (eligible)
    pending_sa = await create_attempt_answer_factory(
        db_session, attempt=att2, question=q_sa, text_answer="Cells produce ATP from sugar.", grading_status=GradingStatus.PENDING
    )
    # Pending essay (eligible)
    pending_essay = await create_attempt_answer_factory(
        db_session, attempt=att2, question=q_essay, text_answer="Climate change impacts biodiversity significantly.", grading_status=GradingStatus.PENDING
    )

    await db_session.commit()

    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])

    with patch("app.ai.grading.service.AIGradingService.grade_subjective_answer") as mock_grade:
        mock_grade.return_value = _mock_ai_result(suggested_marks=4.0, max_marks=5.0)

        res = await teacher_client.post(
            f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
            json={"limit": 20, "regenerateExisting": False},
        )
        assert res.status_code == 200
        data = res.json()

        # Eligible should be exactly 2 (pending_sa and pending_essay)
        assert data["eligibleCount"] == 2
        assert data["processedCount"] == 2
        assert data["failedCount"] == 0
        assert data["remainingCount"] == 0

    # Invariant checks on database entities:
    # 1. Graded answer was completely untouched
    await db_session.refresh(graded_sa)
    assert graded_sa.marksAwarded == 4.5
    assert graded_sa.gradingStatus == GradingStatus.MANUALLY_GRADED
    assert graded_sa.gradedBy == bulk_setup["teacher_user"].id
    assert graded_sa.aiSuggestedMarks is None

    # 2. MCQ answer untouched
    await db_session.refresh(mcq_ans)
    assert mcq_ans.marksAwarded == 2.0
    assert mcq_ans.aiSuggestedMarks is None

    # 3. Pending answer has AI draft proposal but marksAwarded NOT finalized
    await db_session.refresh(pending_sa)
    assert pending_sa.aiSuggestedMarks == 4.0
    assert pending_sa.gradingStatus == GradingStatus.PENDING
    assert pending_sa.marksAwarded == 0.0  # default unfinalized marks
    assert pending_sa.gradedBy is None
    assert pending_sa.gradedAt is None

    # 4. Attempt status was NOT changed to GRADED
    await db_session.refresh(att2)
    assert att2.status == StudentExamStatus.SUBMITTED


# ==============================================================================
# EXISTING AI PROPOSALS SKIPPED / REGENERATED (Part 3, 23)
# ==============================================================================

@pytest.mark.asyncio
async def test_existing_ai_proposals_skipped_by_default(auth_client_factory, db_session, bulk_setup):
    """By default, answers with existing AI proposals are skipped.
    With regenerateExisting=True, they are evaluated again."""
    exam = bulk_setup["exam"]
    att = bulk_setup["attempts"][0]
    q_sa = bulk_setup["q_sa"]

    ans = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Cell respiration produces energy.", grading_status=GradingStatus.PENDING
    )
    ans.aiSuggestedMarks = 3.0
    ans.aiConfidence = "MEDIUM"
    ans.aiFeedback = "Old AI proposal"
    await db_session.commit()

    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])

    # 1. Default (regenerateExisting=False) -> should find 0 eligible answers
    res1 = await teacher_client.post(
        f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
        json={"regenerateExisting": False},
    )
    assert res1.status_code == 200
    assert res1.json()["eligibleCount"] == 0
    assert res1.json()["processedCount"] == 0

    # 2. Explicit regenerateExisting=True -> evaluates answer
    with patch("app.ai.grading.service.AIGradingService.grade_subjective_answer") as mock_grade:
        mock_grade.return_value = _mock_ai_result(suggested_marks=4.5, max_marks=5.0)

        res2 = await teacher_client.post(
            f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
            json={"regenerateExisting": True},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["eligibleCount"] == 1
        assert data2["processedCount"] == 1

        await db_session.refresh(ans)
        assert ans.aiSuggestedMarks == 4.5


# ==============================================================================
# FAILURE ISOLATION (Part 10, 24)
# ==============================================================================

@pytest.mark.asyncio
async def test_failure_isolation_in_batch(auth_client_factory, db_session, bulk_setup):
    """When one answer in a batch fails, other valid answers must still succeed and be saved."""
    exam = bulk_setup["exam"]
    att = bulk_setup["attempts"][0]
    q_sa = bulk_setup["q_sa"]
    q_essay = bulk_setup["q_essay"]

    ans1 = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Answer 1", grading_status=GradingStatus.PENDING
    )
    ans2 = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_essay, text_answer="Answer 2 fails", grading_status=GradingStatus.PENDING
    )

    await db_session.commit()

    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])

    async def mock_grading_fn(*args, **kwargs):
        if "fails" in kwargs.get("student_answer", ""):
            raise GradingContextMissingError("Both reference answer and rubric missing.")
        return _mock_ai_result(suggested_marks=5.0, max_marks=5.0)

    with patch("app.ai.grading.service.AIGradingService.grade_subjective_answer", side_effect=mock_grading_fn):
        res = await teacher_client.post(
            f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
            json={"limit": 20},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["eligibleCount"] == 2
        assert data["processedCount"] == 1
        assert data["failedCount"] == 1

        results = data["results"]
        assert len(results) == 2
        res1 = next(r for r in results if r["answerId"] == ans1.id)
        assert res1["status"] == "AI_PROPOSAL_CREATED"
        res2 = next(r for r in results if r["answerId"] == ans2.id)
        assert res2["status"] == "FAILED"
        assert "reference answer and rubric missing" in res2["message"]

    # Verify ans1 was persisted
    await db_session.refresh(ans1)
    assert ans1.aiSuggestedMarks == 5.0

    # Verify ans2 remains un-graded
    await db_session.refresh(ans2)
    assert ans2.aiSuggestedMarks is None


# ==============================================================================
# PROVIDER RATE LIMIT HANDLING (Part 21)
# ==============================================================================

@pytest.mark.asyncio
async def test_provider_rate_limit_stops_batch(auth_client_factory, db_session, bulk_setup):
    """When a rate limit occurs, current answer fails and subsequent batch is stopped safely."""
    exam = bulk_setup["exam"]
    att = bulk_setup["attempts"][0]
    q_sa = bulk_setup["q_sa"]
    q_essay = bulk_setup["q_essay"]

    ans1 = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Answer 1 rate limited", grading_status=GradingStatus.PENDING
    )
    ans2 = await create_attempt_answer_factory(
        db_session, attempt=att, question=q_essay, text_answer="Answer 2 should be skipped", grading_status=GradingStatus.PENDING
    )
    await db_session.commit()

    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])

    async def mock_rate_limit(*args, **kwargs):
        raise AIGradingProviderError("AI grading service rate limit reached. Please grade manually.")

    with patch("app.ai.grading.service.AIGradingService.grade_subjective_answer", side_effect=mock_rate_limit):
        res = await teacher_client.post(
            f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
            json={"limit": 20},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["failedCount"] == 1
        assert data["skippedCount"] == 1

        results = data["results"]
        assert results[0]["status"] == "FAILED"
        assert "rate limit" in results[0]["message"].lower()
        assert results[1]["status"] == "SKIPPED"


# ==============================================================================
# BATCH LIMIT BOUNDS (Part 7)
# ==============================================================================

@pytest.mark.asyncio
async def test_bulk_request_limit_validation(auth_client_factory, bulk_setup):
    """Enforces that limit must be between 1 and 25."""
    exam = bulk_setup["exam"]
    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])

    # limit > 25 -> 422 Unprocessable Entity
    res = await teacher_client.post(
        f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
        json={"limit": 50},
    )
    assert res.status_code == 422

    # limit < 1 -> 422
    res2 = await teacher_client.post(
        f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
        json={"limit": 0},
    )
    assert res2.status_code == 422


# ==============================================================================
# AUDIT LOGGING (Part 20)
# ==============================================================================

@pytest.mark.asyncio
async def test_bulk_grading_audit_logging(auth_client_factory, db_session, bulk_setup):
    """Verifies AI_BULK_GRADING_STARTED and AI_BULK_GRADING_COMPLETED events are recorded."""
    exam = bulk_setup["exam"]
    att = bulk_setup["attempts"][0]
    q_sa = bulk_setup["q_sa"]

    await create_attempt_answer_factory(
        db_session, attempt=att, question=q_sa, text_answer="Answer for audit test", grading_status=GradingStatus.PENDING
    )
    await db_session.commit()

    teacher_client = await auth_client_factory(bulk_setup["teacher_user"])

    with patch("app.ai.grading.service.AIGradingService.grade_subjective_answer") as mock_grade:
        mock_grade.return_value = _mock_ai_result(suggested_marks=4.0, max_marks=5.0)

        res = await teacher_client.post(
            f"/api/v1/exams/{exam.id}/grading/ai-evaluate-pending",
            json={"limit": 20},
        )
        assert res.status_code == 200

    # Query audit logs
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.resourceId == exam.id,
            AuditLog.action.in_([
                AuditAction.AI_BULK_GRADING_STARTED,
                AuditAction.AI_BULK_GRADING_COMPLETED,
            ]),
        )
        .order_by(AuditLog.timestamp.asc())
    )
    logs = (await db_session.execute(stmt)).scalars().all()
    assert len(logs) == 2
    assert logs[0].action == AuditAction.AI_BULK_GRADING_STARTED
    assert logs[1].action == AuditAction.AI_BULK_GRADING_COMPLETED
    assert logs[1].metadata_["processedCount"] == 1
