"""Exam, Section, Question and Option test factory."""

import uuid
from datetime import UTC, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Exam,
    ExamSection,
    ExamType,
    Question,
    QuestionOption,
    QuestionType,
    Subject,
    Teacher,
)
from tests.factories.teacher_factory import create_teacher_factory


async def create_exam_factory(
    session: AsyncSession,
    *,
    teacher: Teacher | None = None,
    name: str = "Mathematics Midterm",
    description: str = "Midterm examination covering units 1-4",
    scheduled_at: datetime | None = None,
    duration: int = 60,
    max_marks: int = 100,
    is_published: bool = True,
    is_public: bool = True,
    is_results_released: bool = False,
    negative_marking: bool = False,
    negative_marks: float = 0.0,
    exam_type: ExamType = ExamType.MIDTERM,
    subject: Subject = Subject.MATHS,
    access_password: str | None = None,
    exam_code: str | None = None,
) -> Exam:
    """Create and persist an Exam record in the test database."""
    unique_suffix = uuid.uuid4().hex[:6].upper()
    if not teacher:
        teacher = await create_teacher_factory(session)

    exam = Exam(
        name=name,
        description=description,
        scheduledAt=scheduled_at or datetime.now(UTC),
        duration=duration,
        maxMarks=max_marks,
        isPublished=is_published,
        isPublic=is_public,
        isResultsReleased=is_results_released,
        negativeMarking=negative_marking,
        negativeMarks=negative_marks,
        type=exam_type,
        subject=subject,
        teacherId=teacher.id,
        accessPassword=access_password,
        examCode=exam_code or f"EXAM-{unique_suffix}",
    )
    session.add(exam)
    await session.flush()
    await session.refresh(exam)
    return exam


async def create_section_factory(
    session: AsyncSession,
    *,
    exam: Exam,
    name: str = "Section A",
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE,
    marks_per_question: int = 5,
    sort_order: int = 1,
    negative_marking: bool = False,
    negative_marks: float = 0.0,
    duration_minutes: int | None = None,
) -> ExamSection:
    """Create and persist an ExamSection record."""
    section = ExamSection(
        examId=exam.id,
        name=name,
        questionType=question_type,
        marksPerQuestion=marks_per_question,
        sortOrder=sort_order,
        negativeMarking=negative_marking,
        negativeMarks=negative_marks,
        durationMinutes=duration_minutes,
    )
    session.add(section)
    await session.flush()
    await session.refresh(section)
    return section


async def create_question_factory(
    session: AsyncSession,
    *,
    exam: Exam,
    section: ExamSection | None = None,
    question_number: int = 1,
    text: str = "What is 2 + 2?",
    marks: int = 5,
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE,
    explanation: str | None = "2 + 2 equals 4",
    options_data: list[dict] | None = None,
) -> Question:
    """Create and persist a Question with Options."""
    q = Question(
        examId=exam.id,
        sectionId=section.id if section else None,
        section=section.name if section else "General",
        questionNumber=question_number,
        text=text,
        marks=marks,
        questionType=question_type,
        explanation=explanation,
    )
    session.add(q)
    await session.flush()
    await session.refresh(q)

    # If options specified, create options
    if options_data:
        for idx, opt in enumerate(options_data):
            option = QuestionOption(
                questionId=q.id,
                optionNumber=idx + 1,
                text=opt.get("text", f"Option {idx + 1}"),
                isCorrect=opt.get("isCorrect", False),
            )
            session.add(option)
        await session.flush()
        await session.refresh(q)

    return q
