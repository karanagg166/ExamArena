"""Database operations for student answer grading and AI proposals."""

from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.schemas.grading import AIGradingResult
from app.core.models import (
    Correctness,
    GradingStatus,
    QuestionType,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
)


async def _recalculate_attempt_score_and_status(
    student_exam_id: str,
    session: AsyncSession,
) -> None:
    """Recalculates total marks obtained for a student attempt and marks GRADED if no answers remain pending."""
    stmt = select(StudentExamAnswer).where(
        StudentExamAnswer.studentExamId == student_exam_id
    )
    answers = (await session.execute(stmt)).scalars().all()

    total_marks = sum(float(a.marksAwarded or 0.0) for a in answers)

    attempt_stmt = select(StudentExam).where(StudentExam.id == student_exam_id)
    attempt = (await session.execute(attempt_stmt)).scalar_one_or_none()
    if attempt:
        attempt.marksObtained = max(0.0, round(total_marks, 2))
        has_pending = any(a.gradingStatus == GradingStatus.PENDING for a in answers)
        if not has_pending and attempt.status == StudentExamStatus.SUBMITTED:
            attempt.status = StudentExamStatus.GRADED
        attempt.updatedAt = datetime.now(UTC)


def _compute_correctness(marks_awarded: float, max_marks: float) -> Correctness:
    """Determines correctness enum from marks awarded relative to maximum question marks."""
    if marks_awarded >= max_marks:
        return Correctness.FULLY_CORRECT
    if marks_awarded > 0:
        return Correctness.PARTIALLY_CORRECT
    return Correctness.INCORRECT


async def save_ai_grading_proposal(
    answer: StudentExamAnswer,
    proposal: AIGradingResult,
    session: AsyncSession,
) -> StudentExamAnswer:
    """Persists an AI grading proposal onto the student answer entity without finalizing marks."""
    answer.aiSuggestedMarks = proposal.suggested_marks
    answer.aiConfidence = (
        proposal.confidence.value
        if hasattr(proposal.confidence, "value")
        else str(proposal.confidence)
    )
    answer.aiFeedback = proposal.feedback
    answer.aiGradingBreakdown = [item.model_dump() for item in proposal.rubric_breakdown]
    answer.aiWarnings = list(proposal.warnings)
    answer.aiGradedAt = datetime.now(UTC)
    answer.updatedAt = datetime.now(UTC)

    await session.commit()
    await session.refresh(answer)
    return answer


async def accept_ai_grading_proposal(
    answer: StudentExamAnswer,
    teacher_user_id: str,
    session: AsyncSession,
) -> StudentExamAnswer:
    """Adopts the AI grading proposal as the final teacher-approved mark and feedback."""
    if answer.aiSuggestedMarks is None:
        raise ValueError("No AI grading proposal available to accept")

    max_marks = float(answer.question.marks if answer.question else 0.0)
    final_marks = float(answer.aiSuggestedMarks)

    answer.marksAwarded = final_marks
    answer.feedback = answer.aiFeedback
    answer.gradedBy = teacher_user_id
    answer.gradedAt = datetime.now(UTC)
    answer.gradingStatus = GradingStatus.MANUALLY_GRADED
    answer.isCorrect = _compute_correctness(final_marks, max_marks)
    answer.updatedAt = datetime.now(UTC)

    await _recalculate_attempt_score_and_status(answer.studentExamId, session)
    await session.commit()
    await session.refresh(answer)
    return answer


async def apply_teacher_grade_override(
    answer: StudentExamAnswer,
    marks: float,
    feedback: str | None,
    teacher_user_id: str,
    session: AsyncSession,
) -> StudentExamAnswer:
    """Applies a manual score override or feedback from the teacher, finalizing the grade."""
    max_marks = float(answer.question.marks if answer.question else 0.0)
    if marks < 0 or marks > max_marks:
        raise ValueError(f"Marks must be between 0 and {max_marks}")

    answer.marksAwarded = marks
    answer.feedback = feedback
    answer.gradedBy = teacher_user_id
    answer.gradedAt = datetime.now(UTC)
    answer.gradingStatus = GradingStatus.MANUALLY_GRADED
    answer.isCorrect = _compute_correctness(marks, max_marks)
    answer.updatedAt = datetime.now(UTC)

    await _recalculate_attempt_score_and_status(answer.studentExamId, session)
    await session.commit()
    await session.refresh(answer)
    return answer


async def reject_ai_grading_proposal(
    answer: StudentExamAnswer,
    session: AsyncSession,
) -> StudentExamAnswer:
    """Rejects/clears the AI grading proposal while leaving the answer in its current state for manual grading."""
    answer.aiSuggestedMarks = None
    answer.aiConfidence = None
    answer.aiFeedback = None
    answer.aiGradingBreakdown = None
    answer.aiWarnings = None
    answer.aiGradedAt = None
    answer.updatedAt = datetime.now(UTC)

    await session.commit()
    await session.refresh(answer)
    return answer


async def get_exam_grading_summary(
    exam_id: str,
    session: AsyncSession,
) -> dict[str, int]:
    """Computes exam-level subjective grading counts: total, pending, aiSuggestionsReady, teacherGraded."""
    gradable_statuses = (
        StudentExamStatus.SUBMITTED,
        StudentExamStatus.GRADED,
        StudentExamStatus.EXPIRED,
    )
    subjective_types = (
        QuestionType.SHORT_ANSWER,
        QuestionType.ESSAY,
    )

    stmt = (
        select(
            func.count(StudentExamAnswer.id).label("total_subjective"),
            func.count(
                case(
                    (
                        (StudentExamAnswer.gradingStatus != GradingStatus.MANUALLY_GRADED)
                        & (StudentExamAnswer.aiSuggestedMarks.is_(None)),
                        StudentExamAnswer.id,
                    ),
                    else_=None,
                )
            ).label("pending"),
            func.count(
                case(
                    (
                        (StudentExamAnswer.gradingStatus != GradingStatus.MANUALLY_GRADED)
                        & (StudentExamAnswer.aiSuggestedMarks.is_not(None)),
                        StudentExamAnswer.id,
                    ),
                    else_=None,
                )
            ).label("ai_suggestions_ready"),
            func.count(
                case(
                    (
                        StudentExamAnswer.gradingStatus == GradingStatus.MANUALLY_GRADED,
                        StudentExamAnswer.id,
                    ),
                    else_=None,
                )
            ).label("teacher_graded"),
        )
        .join(StudentExam, StudentExamAnswer.studentExamId == StudentExam.id)
        .where(
            StudentExam.examId == exam_id,
            StudentExam.status.in_(gradable_statuses),
            StudentExamAnswer.questionType.in_(subjective_types),
        )
    )

    row = (await session.execute(stmt)).one()
    return {
        "totalSubjectiveAnswers": int(row.total_subjective or 0),
        "pending": int(row.pending or 0),
        "aiSuggestionsReady": int(row.ai_suggestions_ready or 0),
        "teacherGraded": int(row.teacher_graded or 0),
    }


async def count_eligible_subjective_answers(
    exam_id: str,
    regenerate_existing: bool,
    session: AsyncSession,
) -> int:
    """Counts pending subjective answers eligible for bulk AI evaluation."""
    gradable_statuses = (
        StudentExamStatus.SUBMITTED,
        StudentExamStatus.GRADED,
        StudentExamStatus.EXPIRED,
    )
    subjective_types = (
        QuestionType.SHORT_ANSWER,
        QuestionType.ESSAY,
    )

    conditions = [
        StudentExam.examId == exam_id,
        StudentExam.status.in_(gradable_statuses),
        StudentExamAnswer.questionType.in_(subjective_types),
        StudentExamAnswer.gradingStatus != GradingStatus.MANUALLY_GRADED,
    ]

    if not regenerate_existing:
        conditions.append(StudentExamAnswer.aiSuggestedMarks.is_(None))

    stmt = (
        select(func.count(StudentExamAnswer.id))
        .join(StudentExam, StudentExamAnswer.studentExamId == StudentExam.id)
        .where(*conditions)
    )

    count = (await session.execute(stmt)).scalar_one()
    return int(count or 0)


async def get_pending_subjective_answers_for_exam(
    exam_id: str,
    regenerate_existing: bool,
    limit: int,
    session: AsyncSession,
) -> list[StudentExamAnswer]:
    """Retrieves a bounded batch of eligible pending subjective answers with questions eagerly loaded."""
    gradable_statuses = (
        StudentExamStatus.SUBMITTED,
        StudentExamStatus.GRADED,
        StudentExamStatus.EXPIRED,
    )
    subjective_types = (
        QuestionType.SHORT_ANSWER,
        QuestionType.ESSAY,
    )

    conditions = [
        StudentExam.examId == exam_id,
        StudentExam.status.in_(gradable_statuses),
        StudentExamAnswer.questionType.in_(subjective_types),
        StudentExamAnswer.gradingStatus != GradingStatus.MANUALLY_GRADED,
    ]

    if not regenerate_existing:
        conditions.append(StudentExamAnswer.aiSuggestedMarks.is_(None))

    stmt = (
        select(StudentExamAnswer)
        .join(StudentExam, StudentExamAnswer.studentExamId == StudentExam.id)
        .where(*conditions)
        .order_by(StudentExamAnswer.createdAt.asc(), StudentExamAnswer.id.asc())
        .limit(limit)
        .options(
            selectinload(StudentExamAnswer.question),
            selectinload(StudentExamAnswer.studentExam).selectinload(StudentExam.exam),
        )
    )

    return list((await session.execute(stmt)).scalars().all())

