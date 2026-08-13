from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.attempts.schemas import (
    AttemptStatus,
    StudentExamCreate,
    StudentExamResponse,
    StudentExamSubmit,
)
from app.core.models import Exam, SelectedOption, StudentExam, StudentExamAnswer
from app.students.crud import get_student_by_user_id

STUDENT_EXAM_OPTIONS = [
    selectinload(StudentExam.answers).selectinload(StudentExamAnswer.selectedOptions),
]


async def start_exam_attempt(
    attempt_data: StudentExamCreate, user_id: str, session: AsyncSession | None = None
) -> StudentExamResponse:
    student = await get_student_by_user_id(user_id, session=session)
    if not student:
        raise ValueError("Only students can start an exam")

    async def _do_start(s: AsyncSession):
        exam_stmt = (
            select(Exam)
            .where(Exam.id == attempt_data.examId)
            .options(selectinload(Exam.questions))
        )
        exam = (await s.execute(exam_stmt)).scalar_one_or_none()
        if not exam:
            raise ValueError("Exam not found")

        # Check for existing attempt
        existing_stmt = (
            select(StudentExam)
            .where(StudentExam.studentId == student.id, StudentExam.examId == exam.id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        existing = (await s.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            return StudentExamResponse.model_validate(existing)

        # Create attempt & answers
        answers_payload = [
            StudentExamAnswer(
                questionId=q.id,
                questionType=q.questionType,
                gradingStatus="PENDING",
            )
            for q in (exam.questions or [])
        ]

        new_attempt = StudentExam(
            studentId=student.id,
            examId=exam.id,
            status=AttemptStatus.IN_PROGRESS,
            startedAt=datetime.now(UTC),
            answers=answers_payload,
        )
        s.add(new_attempt)
        await s.commit()

        res_stmt = (
            select(StudentExam)
            .where(StudentExam.id == new_attempt.id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        attempt_obj = (await s.execute(res_stmt)).scalar_one()
        return StudentExamResponse.model_validate(attempt_obj)

    if session:
        return await _do_start(session)
    async with db.get_session() as s:
        return await _do_start(s)


async def get_attempt_by_id(
    attempt_id: str, session: AsyncSession | None = None
) -> StudentExamResponse | None:

    async def _do_get(s: AsyncSession):
        stmt = (
            select(StudentExam)
            .where(StudentExam.id == attempt_id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        attempt_model = (await s.execute(stmt)).scalar_one_or_none()
        return (
            StudentExamResponse.model_validate(attempt_model) if attempt_model else None
        )

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def submit_exam_attempt(
    submit_data: StudentExamSubmit, user_id: str, session: AsyncSession | None = None
) -> StudentExamResponse:
    student = await get_student_by_user_id(user_id, session=session)
    attempt = await get_attempt_by_id(submit_data.id, session=session)
    if not attempt:
        raise ValueError("Attempt not found")

    if student and attempt.studentId != student.id:
        raise ValueError("Not authorized to submit this attempt")

    async def _do_submit(s: AsyncSession):
        for ans in submit_data.answers:
            ans_stmt = select(StudentExamAnswer).where(StudentExamAnswer.id == ans.id)
            db_ans = (await s.execute(ans_stmt)).scalar_one_or_none()
            if db_ans:
                if ans.textAnswer is not None:
                    db_ans.textAnswer = ans.textAnswer
                if ans.selectedOptions is not None:
                    # Delete existing selectedOptions for this answer
                    await s.execute(
                        delete(SelectedOption).where(
                            SelectedOption.studentExamAnswerId == ans.id
                        )
                    )
                    db_ans.selectedOptions = [
                        SelectedOption(optionId=o.optionId) for o in ans.selectedOptions
                    ]

        attempt_stmt = select(StudentExam).where(StudentExam.id == submit_data.id)
        db_attempt = (await s.execute(attempt_stmt)).scalar_one_or_none()
        if db_attempt:
            db_attempt.status = AttemptStatus.SUBMITTED
            db_attempt.submittedAt = datetime.now(UTC)

        await s.commit()

        res_stmt = (
            select(StudentExam)
            .where(StudentExam.id == submit_data.id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        updated = (await s.execute(res_stmt)).scalar_one()
        return StudentExamResponse.model_validate(updated)

    if session:
        return await _do_submit(session)
    async with db.get_session() as s:
        return await _do_submit(s)
