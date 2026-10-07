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
