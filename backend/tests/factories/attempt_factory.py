"""StudentExam attempt and answer test factory."""

from datetime import UTC, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Correctness,
    Exam,
    GradingStatus,
    Question,
    SelectedOption,
    Student,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
)


async def create_attempt_factory(
    session: AsyncSession,
    *,
    exam: Exam,
    student: Student,
    status: StudentExamStatus = StudentExamStatus.IN_PROGRESS,
    marks_obtained: float = 0.0,
    started_at: datetime | None = None,
    submitted_at: datetime | None = None,
) -> StudentExam:
    """Create and persist a StudentExam attempt."""
    attempt = StudentExam(
        examId=exam.id,
        studentId=student.id,
        status=status,
        marksObtained=marks_obtained,
        startedAt=started_at or datetime.now(UTC),
        submittedAt=submitted_at,
    )
    session.add(attempt)
    await session.flush()
    await session.refresh(attempt)
    return attempt


async def create_attempt_answer_factory(
    session: AsyncSession,
    *,
    attempt: StudentExam,
    question: Question,
    text_answer: str | None = None,
    selected_option_ids: list[str] | None = None,
    marks_awarded: float = 0.0,
    is_correct: Correctness | None = None,
    grading_status: GradingStatus = GradingStatus.PENDING,
) -> StudentExamAnswer:
    """Create and persist a StudentExamAnswer with selected options."""
    answer = StudentExamAnswer(
        studentExamId=attempt.id,
        questionId=question.id,
        questionType=question.questionType,
        textAnswer=text_answer,
        marksAwarded=marks_awarded,
        isCorrect=is_correct,
        gradingStatus=grading_status,
    )
    session.add(answer)
    await session.flush()
    await session.refresh(answer)

    if selected_option_ids:
        for opt_id in selected_option_ids:
            sel_opt = SelectedOption(
                studentExamAnswerId=answer.id,
                optionId=opt_id,
            )
            session.add(sel_opt)
        await session.flush()

    return answer
