"""Pydantic schemas for structured question paper extraction."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtractedQuestionType(StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"
    UNKNOWN = "UNKNOWN"


class ExtractedConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ExtractedOption(BaseModel):
    label: str | None = Field(
        default=None,
        description="Option label if present in document, e.g. A, B, C, D, (a), (i)",
    )
    text: str = Field(description="Content text of the option")
    is_correct: bool | None = Field(
        default=None,
        description="Explicitly indicated correct answer if stated in paper. MUST be null unless explicitly marked in source.",
    )

    model_config = ConfigDict(extra="ignore")


class ExtractedQuestion(BaseModel):
    question_number: str | None = Field(
        default=None,
        description="Original question number from document, e.g. '1', '1(a)', 'Q2', 'Section B Q1'",
    )
    question_type: ExtractedQuestionType = Field(
        default=ExtractedQuestionType.MULTIPLE_CHOICE,
        description="Mapped question type conforming to ExamArena standard types or UNKNOWN",
    )
    text: str = Field(description="Full text / prompt of the question")
    marks: float | None = Field(
        default=None,
        description="Marking value if present in document. Must be null if absent.",
    )
    options: list[ExtractedOption] = Field(
        default_factory=list,
        description="List of options for objective questions (MCQ, MSQ, True/False)",
    )
    section: str | None = Field(
        default=None,
        description="Section heading or grouping under which this question appeared (e.g. 'Section A')",
    )
    instructions: str | None = Field(
        default=None,
        description="Specific instructions for this question if any",
    )
    image_reference: str | None = Field(
        default=None,
        description="Reference or caption of any diagram/image in the source document",
    )
    confidence: ExtractedConfidence = Field(
        default=ExtractedConfidence.HIGH,
        description="Extraction confidence level (HIGH, MEDIUM, LOW)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Ambiguities or notes for teacher review (e.g. missing marks, unclear type)",
    )

    model_config = ConfigDict(extra="ignore")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        trimmed = (v or "").strip()
        if not trimmed:
            return "Untitled Question"
        return trimmed


class ExtractedQuestionPaper(BaseModel):
    title: str | None = Field(
        default=None, description="Title of examination paper if detected"
    )
    subject: str | None = Field(
        default=None, description="Subject detected from header"
    )
    total_marks: float | None = Field(
        default=None, description="Total maximum marks declared in header"
    )
    duration_minutes: int | None = Field(
        default=None, description="Total duration in minutes declared in header"
    )
    instructions: list[str] = Field(
        default_factory=list, description="General exam instructions detected"
    )
    questions: list[ExtractedQuestion] = Field(
        default_factory=list, description="Extracted questions in paper order"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Document-level warnings or extraction caveats"
    )

    model_config = ConfigDict(extra="ignore")
