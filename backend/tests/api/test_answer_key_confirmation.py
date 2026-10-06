"""Database regressions for exact-set Answer Key confirmation."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.ai.schemas.answer_key import MatchedAnswer, MatchStatus
from app.answer_keys.crud import (
    create_answer_key_import,
    update_answer_key_import_success,
)
from app.answer_keys.service import confirm_answer_key_import
from app.core.models import (
    AnswerKeyImportSourceType,
    Question,
    QuestionOption,
    QuestionType,
)
from tests.factories.exam_factory import create_exam_factory, create_question_factory


async def make_draft(session, kind, initial):
    exam = await create_exam_factory(session)
    labels = (
        ["True", "False"]
        if kind == "TRUE_FALSE" and len(initial) == 2
        else list("ABCD"[: len(initial)])
    )
    question = await create_question_factory(
        session,
        exam=exam,
        question_type=QuestionType(kind),
        explanation=None,
        options_data=[
            dict(text=label, isCorrect=correct)
            for label, correct in zip(labels, initial, strict=True)
        ],
    )
    options = list(
        (
            await session.execute(
                select(QuestionOption)
                .where(QuestionOption.questionId == question.id)
                .order_by(QuestionOption.optionNumber)
            )
        ).scalars()
    )
    record = await create_answer_key_import(
        exam_id=exam.id,
        teacher_id=exam.teacherId,
        original_file_name="key.pdf",
        file_type="application/pdf",
        file_size=10,
        file_path="mock.pdf",
        source_type=AnswerKeyImportSourceType.PDF_TEXT,
        session=session,
    )
    await update_answer_key_import_success(
        import_id=record.id,
        source_type=AnswerKeyImportSourceType.PDF_TEXT,
        extracted_text="synthetic",
        raw_extraction={},
        validated_extraction=dict(exam_id=exam.id, answers=[]),
        session=session,
    )
    await session.commit()
    return record, question, options


@pytest.mark.parametrize(
    "kind,initial,selected,overwrite,expected",
    [
        ("MULTIPLE_SELECT", [False] * 4, [0, 2], False, [True, False, True, False]),
        (
            "MULTIPLE_SELECT",
            [True, True, False, False],
            [2, 3],
            True,
            [False, False, True, True],
        ),
        (
            "MULTIPLE_SELECT",
            [True, True, False, False],
            [2, 3],
            False,
            [True, True, False, False],
        ),
        (
            "MULTIPLE_CHOICE",
            [True, True, False, False],
            [2],
            True,
            [False, False, True, False],
        ),
        ("TRUE_FALSE", [True, False], [1], True, [False, True]),
        ("MULTIPLE_SELECT", [False] * 4, [0, 0, 2], False, [True, False, True, False]),
    ],
)
async def test_confirmation_exact_sets_and_idempotency(
    db_session, kind, initial, selected, overwrite, expected
):
    record, question, options = await make_draft(db_session, kind, initial)
    item = MatchedAnswer(
        question_reference="1",
        status=MatchStatus.MATCHED,
        matched_question_id=question.id,
        matched_option_ids=[options[i].id for i in selected],
    )
    result = await confirm_answer_key_import(record.id, "user", overwrite, [item])
    assert result.updatedQuestionsCount == int(initial != expected)

    async def current_state():
        return [
            o.isCorrect
            for o in (
                await db_session.execute(
                    select(QuestionOption)
                    .where(QuestionOption.questionId == question.id)
                    .order_by(QuestionOption.optionNumber)
                    .execution_options(populate_existing=True)
                )
            ).scalars()
        ]

    assert await current_state() == expected
    again = await confirm_answer_key_import(record.id, "user", overwrite, [item])
    assert again.updatedQuestionsCount == 0
    assert await current_state() == expected


@pytest.mark.parametrize(
    "kind,selected",
    [
        ("MULTIPLE_CHOICE", [0, 1]),
        ("TRUE_FALSE", [0, 1]),
        ("MULTIPLE_SELECT", []),
        ("MULTIPLE_SELECT", [0, "foreign"]),
    ],
)
async def test_confirmation_rejects_invalid_sets(db_session, kind, selected):
    record, question, options = await make_draft(db_session, kind, [False] * 4)
    item = MatchedAnswer(
        question_reference="1",
        status=MatchStatus.MATCHED,
        matched_question_id=question.id,
        matched_option_ids=[
            options[i].id if isinstance(i, int) else i for i in selected
        ],
    )
    with pytest.raises(HTTPException) as exc:
        await confirm_answer_key_import(record.id, "user", True, [item])
    assert exc.value.status_code == 400
    states = list(
        (
            await db_session.execute(
                select(QuestionOption)
                .where(QuestionOption.questionId == question.id)
                .execution_options(populate_existing=True)
            )
        ).scalars()
    )
    assert all(not option.isCorrect for option in states)


@pytest.mark.parametrize("kind", ["SHORT_ANSWER", "ESSAY"])
async def test_subjective_confirmation(db_session, kind):
    record, question, _ = await make_draft(db_session, kind, [])
    item = MatchedAnswer(
        question_reference="1",
        status=MatchStatus.MATCHED,
        matched_question_id=question.id,
        selected_options=[],
        matched_option_ids=[],
        reference_answer="Explicit solution",
        explanation="Explicit explanation",
        rubric=[
            dict(criterion="Definition", marks=2),
            dict(criterion="Reasoning", marks=3),
        ],
    )
    await confirm_answer_key_import(record.id, "user", False, [item])
    updated = (
        await db_session.execute(
            select(Question)
            .where(Question.id == question.id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert updated.referenceAnswer == "Explicit solution"
    assert updated.explanation == "Explicit explanation"
    assert sum(c["marks"] for c in updated.gradingRubric) == 5


async def test_confirmation_does_not_apply_ambiguous_partial_mapping(db_session):
    record, question, options = await make_draft(
        db_session, "MULTIPLE_SELECT", [False] * 4
    )
    item = MatchedAnswer(
        question_reference="1",
        status=MatchStatus.AMBIGUOUS,
        matched_question_id=question.id,
        matched_option_ids=[options[0].id],
    )
    with pytest.raises(HTTPException) as exc:
        await confirm_answer_key_import(record.id, "user", True, [item])
    assert exc.value.status_code == 400
    states = list(
        (
            await db_session.execute(
                select(QuestionOption)
                .where(QuestionOption.questionId == question.id)
                .execution_options(populate_existing=True)
            )
        ).scalars()
    )
    assert all(not option.isCorrect for option in states)
