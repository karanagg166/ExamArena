"""Service boundary for AI-assisted subjective grading using Cohere."""

import json
import logging
from typing import Any

from app.ai.clients.cohere_client import (
    CohereAPIError,
    CohereClient,
    CohereConfigurationError,
    CohereRateLimitError,
    CohereTimeoutError,
)
from app.ai.prompts.grading import (
    SYSTEM_AI_GRADING_PROMPT,
    build_grading_user_prompt,
)
from app.ai.schemas.grading import (
    AIGradingResult,
    GradingConfidence,
    RubricGrade,
)
from app.core.models import QuestionType

logger = logging.getLogger(__name__)


class GradingEligibilityError(ValueError):
    """Raised when AI grading is requested for an ineligible question type (e.g. objective questions)."""

    pass


class GradingContextMissingError(ValueError):
    """Raised when both reference answer and rubric are absent, making reliable AI grading impossible."""

    pass


class AIGradingValidationError(ValueError):
    """Raised when the AI returns invalid scores violating server-side grading invariants."""

    pass


class AIGradingProviderError(RuntimeError):
    """Raised when Cohere API encounters a connection, rate limit, timeout, or provider failure."""

    pass


def validate_grading_eligibility(question_type: QuestionType | str) -> None:
    """Explicitly verify that the question is subjective.

    AI grading is strictly reserved for SHORT_ANSWER and ESSAY.
    Objective questions (MULTIPLE_CHOICE, MULTIPLE_SELECT, TRUE_FALSE) are rejected.
    """
    qt_str = question_type.value if hasattr(question_type, "value") else str(question_type)
    if qt_str not in (QuestionType.SHORT_ANSWER.value, QuestionType.ESSAY.value):
        raise GradingEligibilityError(
            f"AI grading is only supported for SHORT_ANSWER and ESSAY questions, received: {qt_str}"
        )


class AIGradingService:
    """Encapsulates AI grading prompt construction, Cohere execution, and invariant enforcement."""

    def __init__(self, client: CohereClient | None = None):
        self.client = client or CohereClient()

    async def grade_subjective_answer(
        self,
        question_text: str,
        question_type: QuestionType | str,
        max_marks: float,
        student_answer: str | None,
        reference_answer: str | None = None,
        grading_rubric: list[dict[str, Any]] | None = None,
        explanation: str | None = None,
        subject: str | None = None,
        exam_title: str | None = None,
    ) -> AIGradingResult:
        """Evaluates a subjective student answer against reference materials and rubrics.

        Enforces all security, context, and mathematical score invariants server-side.
        """
        # 1. Eligibility guard
        validate_grading_eligibility(question_type)
        qt_str = question_type.value if hasattr(question_type, "value") else str(question_type)

        clean_student_answer = (student_answer or "").strip()
        clean_reference = (reference_answer or "").strip() or None
        has_rubric = bool(grading_rubric and len(grading_rubric) > 0)
        has_reference = clean_reference is not None

        # 2. Context verification (Part 7)
        if not has_rubric and not has_reference:
            raise GradingContextMissingError(
                "Both reference answer and grading rubric are missing. Teacher manual grading required."
            )

        context_warnings: list[str] = []
        effective_rubric = list(grading_rubric) if has_rubric else []

        if not has_rubric and has_reference:
            context_warnings.append("Grading rubric not provided")
            # Synthesize single rubric criterion encompassing full question marks
            effective_rubric = [
                {
                    "criterion": "Overall Answer Quality and Accuracy",
                    "marks": float(max_marks),
                    "description": "Comprehensive evaluation against reference answer",
                }
            ]
        elif has_rubric and not has_reference:
            context_warnings.append("Reference answer not provided")

        # 3. Validate rubric criterion marks vs question max marks (Part 9)
        rubric_sum = sum(float(c.get("marks", 0.0)) for c in effective_rubric)
        if rubric_sum > max_marks:
            context_warnings.append(
                f"Rubric total marks ({rubric_sum}) exceeds question maximum marks ({max_marks}). Suggested marks will be capped to {max_marks}."
            )

        # 4. Handle empty/whitespace student answer locally without calling Cohere (Part 29)
        if not clean_student_answer:
            breakdown: list[RubricGrade] = []
            for criterion in effective_rubric:
                c_name = criterion.get("criterion", "Criterion")
                c_max = float(criterion.get("marks", 0.0))
                breakdown.append(
                    RubricGrade(
                        criterion=c_name,
                        max_marks=c_max,
                        awarded_marks=0.0,
                        justification="No answer provided.",
                    )
                )
            return AIGradingResult(
                suggested_marks=0.0,
                max_marks=float(max_marks),
                rubric_breakdown=breakdown,
                feedback="No answer provided.",
                confidence=GradingConfidence.HIGH,
                warnings=context_warnings,
            )

        # 5. Build prompt payload
        user_prompt = build_grading_user_prompt(
            question_text=question_text,
            question_type=qt_str,
            max_marks=float(max_marks),
            student_answer=clean_student_answer,
            reference_answer=clean_reference,
            grading_rubric=effective_rubric,
            explanation=explanation,
            subject=subject,
            exam_title=exam_title,
        )

        messages = [
            {"role": "system", "content": SYSTEM_AI_GRADING_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        schema = AIGradingResult.model_json_schema()

        # 6. Call Cohere
        try:
            raw_json, _ = await self.client.extract_structured_json(
                messages=messages,
                schema=schema,
                temperature=0.0,
            )
        except CohereConfigurationError as exc:
            logger.error("Cohere configuration error: %s", exc)
            raise AIGradingProviderError(f"AI grading configuration error: {exc}") from exc
        except CohereRateLimitError as exc:
            logger.warning("Cohere rate limit reached during grading: %s", exc)
            raise AIGradingProviderError("AI grading service rate limit reached. Please grade manually or retry later.") from exc
        except CohereTimeoutError as exc:
            logger.warning("Cohere request timed out during grading: %s", exc)
            raise AIGradingProviderError("AI grading request timed out. Please grade manually or retry later.") from exc
        except CohereAPIError as exc:
            logger.error("Cohere API error during grading: %s", exc)
            raise AIGradingProviderError("AI grading provider error encountered.") from exc
        except Exception as exc:
            logger.error("Unexpected error invoking Cohere grading: %s", exc)
            raise AIGradingProviderError(f"AI grading provider failed: {exc}") from exc

        # 7. Parse and validate structured output (Part 10)
        try:
            data = json.loads(raw_json)
            result = AIGradingResult.model_validate(data)
        except Exception as exc:
            logger.error("Malformed structured output from Cohere: %s", exc)
            raise AIGradingValidationError(f"AI grading returned invalid structured output: {exc}") from exc

        # 8. Server-side Score Invariants and Normalization (Parts 11, 12)
        # Check criteria awarded bounds
        for item in result.rubric_breakdown:
            if item.awarded_marks < 0:
                raise AIGradingValidationError(
                    f"Invalid negative marks awarded on criterion '{item.criterion}': {item.awarded_marks}"
                )
            if item.awarded_marks > item.max_marks:
                # Allow tiny floating drift (e.g. 1.0001 vs 1.0)
                if item.awarded_marks - item.max_marks <= 0.05:
                    item.awarded_marks = item.max_marks
                else:
                    raise AIGradingValidationError(
                        f"Criterion '{item.criterion}' awarded marks ({item.awarded_marks}) exceeds criterion max ({item.max_marks})"
                    )

        # Check total vs rubric sum
        calculated_sum = round(sum(item.awarded_marks for item in result.rubric_breakdown), 2)
        diff = abs(calculated_sum - result.suggested_marks)

        if diff <= 0.05:
            # Deterministically align suggested_marks with sum of rubric items
            result.suggested_marks = calculated_sum
        else:
            raise AIGradingValidationError(
                f"Inconsistent AI scoring: rubric sum ({calculated_sum}) does not match suggested total ({result.suggested_marks})"
            )

        # Enforce question max marks bounds
        if result.suggested_marks < 0:
            raise AIGradingValidationError(f"Suggested total marks cannot be negative: {result.suggested_marks}")

        if result.suggested_marks > max_marks:
            result.suggested_marks = float(max_marks)
            context_warnings.append(
                f"AI suggested marks capped to question maximum marks ({max_marks})."
            )

        result.max_marks = float(max_marks)

        # Merge context warnings
        for w in context_warnings:
            if w not in result.warnings:
                result.warnings.append(w)

        # Degrade confidence if critical reference/rubric context was incomplete
        if not has_rubric or not has_reference:
            if result.confidence == GradingConfidence.HIGH:
                result.confidence = GradingConfidence.MEDIUM

        return result
