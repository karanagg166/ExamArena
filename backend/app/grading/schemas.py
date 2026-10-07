"""Pydantic schemas for student answer grading APIs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RubricGradeResponse(BaseModel):
    criterion: str
    maxMarks: float
    awardedMarks: float
    justification: str

    model_config = ConfigDict(from_attributes=True)


class AIGradingProposalResponse(BaseModel):
    answerId: str
    suggestedMarks: float
    maxMarks: float
    rubricBreakdown: list[RubricGradeResponse] = Field(default_factory=list)
    feedback: str
    confidence: str
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TeacherGradeUpdateRequest(BaseModel):
    marks: float = Field(ge=0, description="Marks to award for this answer")
    feedback: str | None = Field(default=None, description="Teacher feedback for the student")

    model_config = ConfigDict(extra="forbid")


class TeacherGradeResponse(BaseModel):
    answerId: str
    studentExamId: str
    questionId: str
    marksAwarded: float
    maxMarks: float
    feedback: str | None = None
    gradingStatus: str
    gradedBy: str | None = None
    gradedAt: datetime | None = None
    isCorrect: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TeacherStudentAnswerDetailResponse(BaseModel):
    id: str
    studentExamId: str
    questionId: str
    questionType: str
    questionNumber: int
    questionText: str
    maxMarks: float
    studentAnswer: str | None = None
    referenceAnswer: str | None = None
    gradingRubric: list[dict[str, Any]] | None = None
    explanation: str | None = None
    aiProposal: AIGradingProposalResponse | None = None
    finalGrade: TeacherGradeResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ExamGradingSummaryResponse(BaseModel):
    examId: str
    totalSubjectiveAnswers: int
    pending: int
    aiSuggestionsReady: int
    teacherGraded: int

    model_config = ConfigDict(from_attributes=True)


class BulkAIEvaluateRequest(BaseModel):
    limit: int = Field(
        default=20,
        ge=1,
        le=25,
        description="Maximum number of subjective answers to evaluate in this batch (max 25)",
    )
    regenerateExisting: bool = Field(
        default=False,
        description="Whether to re-evaluate answers that already have an existing AI proposal",
    )

    model_config = ConfigDict(extra="forbid")


class BulkAIEvaluationItemResult(BaseModel):
    answerId: str
    studentExamId: str
    status: str  # "AI_PROPOSAL_CREATED", "FAILED", "SKIPPED"
    message: str | None = None
    suggestedMarks: float | None = None

    model_config = ConfigDict(from_attributes=True)


class BulkAIEvaluateResponse(BaseModel):
    examId: str
    eligibleCount: int
    requestedCount: int
    processedCount: int
    failedCount: int
    skippedCount: int
    remainingCount: int
    results: list[BulkAIEvaluationItemResult] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

