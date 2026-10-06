"""Unit tests for AIGradingService with mocked Cohere client."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.clients.cohere_client import (
    CohereAPIError,
    CohereClient,
    CohereConfigurationError,
    CohereRateLimitError,
    CohereTimeoutError,
)
from app.ai.grading.service import (
    AIGradingProviderError,
    AIGradingService,
    AIGradingValidationError,
    GradingContextMissingError,
    GradingEligibilityError,
)
from app.ai.schemas.grading import GradingConfidence
from app.core.models import QuestionType


@pytest.mark.asyncio
async def test_eligibility_guards_reject_objective_questions():
    service = AIGradingService(client=MagicMock(spec=CohereClient))

    for invalid_type in [
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.MULTIPLE_SELECT,
        QuestionType.TRUE_FALSE,
        "MULTIPLE_CHOICE",
    ]:
        with pytest.raises(GradingEligibilityError) as exc_info:
            await service.grade_subjective_answer(
                question_text="Sample question",
                question_type=invalid_type,
                max_marks=2.0,
                student_answer="Option A",
                reference_answer="Option A",
            )
        assert "only supported for SHORT_ANSWER and ESSAY" in str(exc_info.value)


@pytest.mark.asyncio
async def test_empty_or_whitespace_student_answer_deterministic():
    mock_client = MagicMock(spec=CohereClient)
    service = AIGradingService(client=mock_client)

    rubric = [
        {"criterion": "Definition", "marks": 2.0},
        {"criterion": "Example", "marks": 3.0},
    ]

    for empty_val in ["", "   ", "\n\t  ", None]:
        result = await service.grade_subjective_answer(
            question_text="Define photosynthesis",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=5.0,
            student_answer=empty_val,
            reference_answer="Photosynthesis is the process...",
            grading_rubric=rubric,
        )

        assert result.suggested_marks == 0.0
        assert result.max_marks == 5.0
        assert result.feedback == "No answer provided."
        assert result.confidence == GradingConfidence.HIGH
        assert len(result.rubric_breakdown) == 2
        assert result.rubric_breakdown[0].awarded_marks == 0.0
        assert result.rubric_breakdown[1].awarded_marks == 0.0
        # Cohere must not be invoked
        mock_client.extract_structured_json.assert_not_called()


@pytest.mark.asyncio
async def test_missing_both_reference_and_rubric_fails():
    service = AIGradingService(client=MagicMock(spec=CohereClient))

    with pytest.raises(GradingContextMissingError) as exc_info:
        await service.grade_subjective_answer(
            question_text="Explain black holes",
            question_type=QuestionType.ESSAY,
            max_marks=10.0,
            student_answer="A black hole is a region of spacetime...",
            reference_answer=None,
            grading_rubric=[],
        )
    assert "Both reference answer and grading rubric are missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_missing_rubric_with_reference_answer():
    mock_client = MagicMock(spec=CohereClient)
    cohere_output = {
        "suggested_marks": 4.0,
        "max_marks": 5.0,
        "rubric_breakdown": [
            {
                "criterion": "Overall Answer Quality and Accuracy",
                "max_marks": 5.0,
                "awarded_marks": 4.0,
                "justification": "Good explanation matching reference answer.",
            }
        ],
        "feedback": "Well explained, missed minor edge case.",
        "confidence": "HIGH",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {"duration_ms": 100})
    )
    service = AIGradingService(client=mock_client)

    result = await service.grade_subjective_answer(
        question_text="What is mitosis?",
        question_type=QuestionType.SHORT_ANSWER,
        max_marks=5.0,
        student_answer="Mitosis is a process of cell duplication...",
        reference_answer="Mitosis is cell division resulting in two identical daughter cells.",
        grading_rubric=None,
    )

    assert result.suggested_marks == 4.0
    assert "Grading rubric not provided" in result.warnings
    assert result.confidence in (GradingConfidence.MEDIUM, GradingConfidence.LOW)


@pytest.mark.asyncio
async def test_missing_reference_answer_with_rubric():
    mock_client = MagicMock(spec=CohereClient)
    rubric = [{"criterion": "Mentions cell division", "marks": 5.0}]
    cohere_output = {
        "suggested_marks": 5.0,
        "max_marks": 5.0,
        "rubric_breakdown": [
            {
                "criterion": "Mentions cell division",
                "max_marks": 5.0,
                "awarded_marks": 5.0,
                "justification": "Directly mentioned cell division.",
            }
        ],
        "feedback": "Correct explanation.",
        "confidence": "HIGH",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {"duration_ms": 100})
    )
    service = AIGradingService(client=mock_client)

    result = await service.grade_subjective_answer(
        question_text="What is mitosis?",
        question_type=QuestionType.SHORT_ANSWER,
        max_marks=5.0,
        student_answer="Mitosis is cell division.",
        reference_answer=None,
        grading_rubric=rubric,
    )

    assert result.suggested_marks == 5.0
    assert "Reference answer not provided" in result.warnings
    assert result.confidence in (GradingConfidence.MEDIUM, GradingConfidence.LOW)


@pytest.mark.asyncio
async def test_rubric_sum_exceeding_max_marks_records_warning():
    mock_client = MagicMock(spec=CohereClient)
    # Question is 5 marks, but rubric sums to 6 marks (2 + 4)
    rubric = [
        {"criterion": "Part 1", "marks": 2.0},
        {"criterion": "Part 2", "marks": 4.0},
    ]
    cohere_output = {
        "suggested_marks": 5.5,
        "max_marks": 6.0,
        "rubric_breakdown": [
            {"criterion": "Part 1", "max_marks": 2.0, "awarded_marks": 2.0, "justification": "Good"},
            {"criterion": "Part 2", "max_marks": 4.0, "awarded_marks": 3.5, "justification": "Decent"},
        ],
        "feedback": "Good attempt",
        "confidence": "HIGH",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {})
    )
    service = AIGradingService(client=mock_client)

    result = await service.grade_subjective_answer(
        question_text="Sample essay",
        question_type=QuestionType.ESSAY,
        max_marks=5.0,
        student_answer="Sample answer content",
        reference_answer="Reference solution",
        grading_rubric=rubric,
    )

    # Must be safely capped at 5.0
    assert result.suggested_marks == 5.0
    assert any("exceeds question maximum marks" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_successful_subjective_grading_with_partial_credit():
    mock_client = MagicMock(spec=CohereClient)
    rubric = [
        {"criterion": "Definition", "marks": 1.0},
        {"criterion": "Mechanism", "marks": 2.0},
        {"criterion": "Example", "marks": 2.0},
    ]
    # AI awards 1.0 + 1.5 + 1.0 = 3.5 / 5.0
    cohere_output = {
        "suggested_marks": 3.5,
        "max_marks": 5.0,
        "rubric_breakdown": [
            {"criterion": "Definition", "max_marks": 1.0, "awarded_marks": 1.0, "justification": "Clear definition."},
            {"criterion": "Mechanism", "max_marks": 2.0, "awarded_marks": 1.5, "justification": "Partially explained steps."},
            {"criterion": "Example", "max_marks": 2.0, "awarded_marks": 1.0, "justification": "One example given, second missing."},
        ],
        "feedback": "Accurate definition and mechanism; provide two distinct examples for full credit.",
        "confidence": "HIGH",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {})
    )
    service = AIGradingService(client=mock_client)

    result = await service.grade_subjective_answer(
        question_text="Explain osmosis with examples.",
        question_type=QuestionType.SHORT_ANSWER,
        max_marks=5.0,
        student_answer="Osmosis is water movement through semipermeable membrane...",
        reference_answer="Osmosis definition, concentration gradient mechanism, potato experiment.",
        grading_rubric=rubric,
    )

    assert result.suggested_marks == 3.5
    assert result.max_marks == 5.0
    assert len(result.rubric_breakdown) == 3
    assert result.rubric_breakdown[0].awarded_marks == 1.0
    assert result.rubric_breakdown[1].awarded_marks == 1.5
    assert result.rubric_breakdown[2].awarded_marks == 1.0
    assert result.confidence == GradingConfidence.HIGH


@pytest.mark.asyncio
async def test_invalid_negative_criterion_score_rejected():
    mock_client = MagicMock(spec=CohereClient)
    cohere_output = {
        "suggested_marks": -1.0,
        "max_marks": 5.0,
        "rubric_breakdown": [
            {"criterion": "Definition", "max_marks": 5.0, "awarded_marks": -1.0, "justification": "Terrible"}
        ],
        "feedback": "Wrong",
        "confidence": "LOW",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {})
    )
    service = AIGradingService(client=mock_client)

    with pytest.raises(AIGradingValidationError):
        await service.grade_subjective_answer(
            question_text="Define Newton's law",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=5.0,
            student_answer="Wrong answer",
            reference_answer="F = ma",
            grading_rubric=[{"criterion": "Definition", "marks": 5.0}],
        )


@pytest.mark.asyncio
async def test_criterion_score_exceeding_max_rejected():
    mock_client = MagicMock(spec=CohereClient)
    cohere_output = {
        "suggested_marks": 3.0,
        "max_marks": 2.0,
        "rubric_breakdown": [
            {"criterion": "Criterion 1", "max_marks": 1.0, "awarded_marks": 3.0, "justification": "Extra marks"}
        ],
        "feedback": "Great",
        "confidence": "HIGH",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {})
    )
    service = AIGradingService(client=mock_client)

    with pytest.raises(AIGradingValidationError):
        await service.grade_subjective_answer(
            question_text="Sample",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=2.0,
            student_answer="Sample answer",
            reference_answer="Reference",
            grading_rubric=[{"criterion": "Criterion 1", "marks": 1.0}],
        )


@pytest.mark.asyncio
async def test_inconsistent_total_marks_rejected():
    mock_client = MagicMock(spec=CohereClient)
    # Sum of items = 1.0 + 1.0 = 2.0, but suggested_marks declares 5.0
    cohere_output = {
        "suggested_marks": 5.0,
        "max_marks": 5.0,
        "rubric_breakdown": [
            {"criterion": "Part 1", "max_marks": 2.5, "awarded_marks": 1.0, "justification": "Ok"},
            {"criterion": "Part 2", "max_marks": 2.5, "awarded_marks": 1.0, "justification": "Ok"},
        ],
        "feedback": "Decent",
        "confidence": "HIGH",
        "warnings": [],
    }
    mock_client.extract_structured_json = AsyncMock(
        return_value=(json.dumps(cohere_output), {})
    )
    service = AIGradingService(client=mock_client)

    with pytest.raises(AIGradingValidationError) as exc_info:
        await service.grade_subjective_answer(
            question_text="Sample",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=5.0,
            student_answer="Sample answer",
            reference_answer="Reference",
            grading_rubric=[{"criterion": "Part 1", "marks": 2.5}, {"criterion": "Part 2", "marks": 2.5}],
        )
    assert "Inconsistent AI scoring" in str(exc_info.value)


@pytest.mark.asyncio
async def test_provider_errors_wrapped_cleanly():
    mock_client = MagicMock(spec=CohereClient)

    for err_cls in [
        CohereTimeoutError("Timed out"),
        CohereRateLimitError("Rate limit"),
        CohereAPIError("API error"),
        CohereConfigurationError("Missing key"),
    ]:
        mock_client.extract_structured_json = AsyncMock(side_effect=err_cls)
        service = AIGradingService(client=mock_client)

        with pytest.raises(AIGradingProviderError):
            await service.grade_subjective_answer(
                question_text="Sample",
                question_type=QuestionType.SHORT_ANSWER,
                max_marks=5.0,
                student_answer="Student answer",
                reference_answer="Reference answer",
                grading_rubric=[{"criterion": "Overall", "marks": 5.0}],
            )


@pytest.mark.asyncio
async def test_malformed_json_from_provider_rejected():
    mock_client = MagicMock(spec=CohereClient)
    mock_client.extract_structured_json = AsyncMock(
        return_value=("NOT_JSON_AT_ALL", {})
    )
    service = AIGradingService(client=mock_client)

    with pytest.raises(AIGradingValidationError):
        await service.grade_subjective_answer(
            question_text="Sample",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=5.0,
            student_answer="Student answer",
            reference_answer="Reference answer",
            grading_rubric=[{"criterion": "Overall", "marks": 5.0}],
        )
