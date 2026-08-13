from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import Question, QuestionOption
from app.questions.schemas import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
)


async def create_question(
    question_data: QuestionCreateRequest, session: AsyncSession | None = None
) -> QuestionResponse:
    opts = []
    if question_data.options:
        opts = [
            QuestionOption(
                text=o.text,
                optionNumber=o.optionNumber,
                isCorrect=o.isCorrect,
                imageUrl=o.imageUrl,
            )
            for o in question_data.options
        ]

    create_data = {
        "text": question_data.text,
        "marks": question_data.marks,
        "questionNumber": question_data.questionNumber,
        "questionType": question_data.questionType,
        "imageUrl": question_data.imageUrl,
        "wordLimit": question_data.wordLimit,
        "explanation": question_data.explanation,
        "section": question_data.section,
        "examId": question_data.examId,
    }

    async def _do_create(s: AsyncSession):
        question = Question(**create_data)
        if opts:
            question.options = opts
        s.add(question)
        await s.commit()
        await s.refresh(question)

        stmt = (
            select(Question)
            .where(Question.id == question.id)
            .options(selectinload(Question.options))
        )
        created = (await s.execute(stmt)).scalar_one()
        return QuestionResponse.model_validate(created)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def update_question(
    question_id: str,
    update_data: QuestionUpdateRequest,
    session: AsyncSession | None = None,
) -> QuestionResponse | None:
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"id", "options"})

    async def _do_update(s: AsyncSession):
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = (await s.execute(stmt)).scalar_one_or_none()
        if not question:
            return None

        for k, v in update_dict.items():
            setattr(question, k, v)

        if update_data.options is not None:
            # Delete existing options
            await s.execute(
                delete(QuestionOption).where(QuestionOption.questionId == question_id)
            )
            question.options = [
                QuestionOption(
                    text=o.text,
                    optionNumber=o.optionNumber,
                    isCorrect=o.isCorrect,
                    imageUrl=o.imageUrl,
                )
                for o in update_data.options
            ]

        await s.commit()

        res_stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        updated = (await s.execute(res_stmt)).scalar_one_or_none()
        return QuestionResponse.model_validate(updated) if updated else None

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def get_question_by_id(
    question_id: str, session: AsyncSession | None = None
) -> QuestionResponse | None:

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = (await s.execute(stmt)).scalar_one_or_none()
        return QuestionResponse.model_validate(question) if question else None

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def delete_question(
    question_id: str, session: AsyncSession | None = None
) -> QuestionResponse | None:

    async def _do_delete(s: AsyncSession):
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        question = (await s.execute(stmt)).scalar_one_or_none()
        if not question:
            return None
        res = QuestionResponse.model_validate(question)
        await s.delete(question)
        await s.commit()
        return res

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)
