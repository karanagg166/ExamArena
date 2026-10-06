"""Pydantic schemas for Answer Key Import API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ai.schemas.answer_key import MatchedAnswer, RubricCriterion
from app.core.models import AnswerKeyImportSourceType, AnswerKeyImportStatus


class AnswerKeyImportResponse(BaseModel):
    id: str
    examId: str
    teacherId: str
    originalFileName: str
    fileType: str
    fileSize: int
    status: AnswerKeyImportStatus
    sourceType: AnswerKeyImportSourceType
    errorMessage: str | None = None
    errorCategory: str | None = None
    createdAt: datetime
    updatedAt: datetime
    completedAt: datetime | None = None
    confirmedAt: datetime | None = None
    matchedCount: int = 0
    ambiguousCount: int = 0
    unmatchedCount: int = 0
    totalAnswers: int = 0
    title: str | None = None
    examReference: str | None = None
    answers: list[MatchedAnswer] | None = None
    warnings: list[str] = Field(default_factory=list)
    storageProvider: str | None = None
    storageUrl: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AnswerKeyImportListItem(BaseModel):
    id: str
    examId: str
    teacherId: str
    originalFileName: str
    fileType: str
    fileSize: int
    status: AnswerKeyImportStatus
    sourceType: AnswerKeyImportSourceType
    matchedCount: int = 0
    totalAnswers: int = 0
    createdAt: datetime
    updatedAt: datetime
    completedAt: datetime | None = None
    confirmedAt: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AnswerKeyImportUpdateRequest(BaseModel):
    title: str | None = None
    answers: list[MatchedAnswer] | None = None

    model_config = ConfigDict(extra="ignore")


class AnswerKeyImportConfirmRequest(BaseModel):
    overwriteExistingAnswers: bool = False
    answers: list[MatchedAnswer] | None = None

    model_config = ConfigDict(extra="ignore")


class AnswerKeyImportConfirmResponse(BaseModel):
    id: str
    examId: str
    status: AnswerKeyImportStatus
    updatedQuestionsCount: int
    confirmedAt: datetime

    model_config = ConfigDict(from_attributes=True)
