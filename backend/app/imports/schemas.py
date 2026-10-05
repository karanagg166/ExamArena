"""Pydantic schemas for Question Paper Import API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ai.schemas.question_paper import (
    ExtractedOption,
    ExtractedQuestion,
    ExtractedQuestionPaper,
)
from app.core.models import QuestionImportSourceType, QuestionImportStatus


class QuestionImportResponse(BaseModel):
    id: str
    examId: str
    teacherId: str
    originalFileName: str
    fileType: str
    fileSize: int
    status: QuestionImportStatus
    sourceType: QuestionImportSourceType
    errorMessage: str | None = None
    errorCategory: str | None = None
    createdAt: datetime
    updatedAt: datetime
    completedAt: datetime | None = None
    confirmedAt: datetime | None = None
    questionCount: int | None = None
    title: str | None = None
    subject: str | None = None
    questions: list[ExtractedQuestion] | None = None
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class QuestionImportListItem(BaseModel):
    id: str
    examId: str
    teacherId: str
    originalFileName: str
    fileType: str
    fileSize: int
    status: QuestionImportStatus
    sourceType: QuestionImportSourceType
    questionCount: int = 0
    createdAt: datetime
    updatedAt: datetime
    completedAt: datetime | None = None
    confirmedAt: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class QuestionImportUpdateRequest(BaseModel):
    title: str | None = None
    subject: str | None = None
    questions: list[ExtractedQuestion] | None = None

    model_config = ConfigDict(extra="ignore")


class QuestionImportConfirmResponse(BaseModel):
    id: str
    examId: str
    status: QuestionImportStatus
    createdQuestionsCount: int
    confirmedAt: datetime

    model_config = ConfigDict(from_attributes=True)
