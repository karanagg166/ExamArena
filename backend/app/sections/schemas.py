import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"


SECTION_NAME_PATTERN = re.compile(r"^Section [A-Z]$")


class SectionBase(BaseModel):
    name: str
    description: str | None = None
    questionType: QuestionType
    marksPerQuestion: int
    durationMinutes: int | None = None

    @field_validator("name")
    @classmethod
    def validate_section_name(cls, v: str) -> str:
        if not SECTION_NAME_PATTERN.match(v):
            raise ValueError(
                'Section name must follow the pattern "Section A", "Section B", etc. '
                "(uppercase letter A-Z only)"
            )
        return v

    @field_validator("marksPerQuestion")
    @classmethod
    def validate_marks(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("marksPerQuestion must be greater than 0")
        return v


class SectionCreateRequest(SectionBase):
    examId: str


class SectionUpdateRequest(BaseModel):
    description: str | None = None
    questionType: QuestionType | None = None
    marksPerQuestion: int | None = None
    durationMinutes: int | None = None

    @field_validator("marksPerQuestion")
    @classmethod
    def validate_marks(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("marksPerQuestion must be greater than 0")
        return v


class SectionResponse(SectionBase):
    id: str
    examId: str
    sortOrder: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)
