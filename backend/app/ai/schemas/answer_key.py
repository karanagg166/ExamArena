"""Pydantic schemas for structured answer key extraction and matching."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.ai.schemas.question_paper import ExtractedConfidence


class MatchStatus(StrEnum):
    MATCHED = "MATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    UNMATCHED = "UNMATCHED"


class RubricCriterion(BaseModel):
    criterion: str = Field(description="Description of the grading criterion or step")
    marks: float = Field(ge=0, description="Marks allocated for this criterion")
    description: str | None = Field(
        default=None, description="Detailed explanation or scoring notes"
    )

    model_config = ConfigDict(extra="ignore")


class ExtractedAnswer(BaseModel):
    question_reference: str = Field(
        description="Question number or identifier as written in the answer key, e.g. '1', 'Q2', '1(a)', 'Question 5'"
    )
    question_text_snippet: str | None = Field(
        default=None,
        description="Brief snippet of the question text if included in the answer key document",
    )
    selected_options: list[str] = Field(
        default_factory=list,
        description="Each explicitly declared correct label or option text as a separate element. MCQ and True/False: one element; Multiple Select: all correct options; subjective: empty list.",
    )

    reference_answer: str | None = Field(
        default=None,
        description="Model answer, solution text, or key points for descriptive/essay/short answer questions",
    )
    explanation: str | None = Field(
        default=None,
        description="Rationale, derivation, or explanation provided for the answer",
    )
    rubric: list[RubricCriterion] = Field(
        default_factory=list,
        description="Grading rubric criteria or mark breakdown if provided",
    )
    marks: float | None = Field(
        default=None,
        description="Marks allocated to this question if specified in the answer key",
    )
    confidence: ExtractedConfidence = Field(
        default=ExtractedConfidence.HIGH,
        description="Extraction confidence level (HIGH, MEDIUM, LOW)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any notes or ambiguities noticed during extraction",
    )

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def read_legacy_selection(cls, data: Any) -> Any:
        if isinstance(data, dict) and "selected_options" not in data:
            data = dict(data)
            value = data.get("selected_option") or data.get("selected_option_text")
            data["selected_options"] = [value] if value else []
        return data


class ExtractedAnswerKey(BaseModel):
    title: str | None = Field(
        default=None, description="Title of the answer key document if detected"
    )
    exam_reference: str | None = Field(
        default=None,
        description="Exam name, subject, or code referenced in the answer key header",
    )
    answers: list[ExtractedAnswer] = Field(
        default_factory=list,
        description="Extracted answer items from the document",
    )
    total_marks: float | None = Field(
        default=None,
        description="Total marks declared in the answer key header if specified",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="General warnings or notes regarding the document structure",
    )

    model_config = ConfigDict(extra="ignore")


class MatchedAnswer(ExtractedAnswer):
    # Matching resolution fields
    status: MatchStatus = MatchStatus.UNMATCHED
    matched_question_id: str | None = None
    matched_question_number: int | None = None
    matched_question_text: str | None = None
    matched_question_type: str | None = None
    matched_option_ids: list[str] = Field(default_factory=list)

    match_confidence: float = 0.0
    match_reason: str | None = None
    candidate_question_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def read_legacy_matched_option(cls, data: Any) -> Any:
        if isinstance(data, dict) and "matched_option_ids" not in data:
            data = dict(data)
            value = data.get("matched_option_id")
            data["matched_option_ids"] = [value] if value else []
        return data


class MatchedAnswerKey(BaseModel):
    import_id: str | None = None
    exam_id: str
    matched_count: int = 0
    ambiguous_count: int = 0
    unmatched_count: int = 0
    total_answers: int = 0
    answers: list[MatchedAnswer] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
