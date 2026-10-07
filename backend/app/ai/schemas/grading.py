"""Pydantic schemas for AI-assisted subjective grading."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class GradingConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RubricGrade(BaseModel):
    criterion: str = Field(description="Rubric criterion name or evaluation step")
    max_marks: float = Field(
        ge=0, description="Maximum marks allocated for this criterion"
    )
    awarded_marks: float = Field(
        ge=0, description="Marks awarded to the student for this criterion"
    )
    justification: str = Field(
        description="Specific pedagogical rationale for the marks awarded on this criterion"
    )

    model_config = ConfigDict(extra="ignore")


class AIGradingResult(BaseModel):
    suggested_marks: float = Field(
        ge=0, description="Total suggested marks awarded for the answer"
    )
    max_marks: float = Field(
        gt=0, description="Maximum possible marks for the question"
    )
    rubric_breakdown: list[RubricGrade] = Field(
        default_factory=list,
        description="Detailed mark breakdown corresponding to each rubric criterion",
    )
    feedback: str = Field(
        description="Constructive, concise feedback explaining what was correct and what was missing"
    )
    confidence: GradingConfidence = Field(
        default=GradingConfidence.HIGH,
        description="Confidence level in the grading proposal (HIGH, MEDIUM, LOW)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Caveats, missing rubric notices, or scoring notes for the teacher",
    )

    model_config = ConfigDict(extra="ignore")
