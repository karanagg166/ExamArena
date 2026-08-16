from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"


class QuestionBase(BaseModel):
    text: str
    marks: int = Field(default=1, gt=0)
    negativeMarks: float | None = Field(default=None, ge=0)
    questionNumber: int = Field(default=1, gt=0)
    questionType: QuestionType = QuestionType.MULTIPLE_CHOICE
    imageUrl: str | None = None
    wordLimit: int | None = Field(default=None, gt=0)
    explanation: str | None = None
    examId: str | None = None
    sectionId: str | None = None
    section: str = "Section A"

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v


class QuestionOptionBase(BaseModel):
    text: str
    optionNumber: int = Field(gt=0)
    imageUrl: str | None = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Option text cannot be empty")
        return v


class QuestionOptionCreate(QuestionOptionBase):
    questionId: str | None = None
    isCorrect: bool


class QuestionOptionResponse(QuestionOptionBase):
    id: str
    questionId: str
    isCorrect: bool

    model_config = ConfigDict(from_attributes=True)


class QuestionOptionUpdate(BaseModel):
    id: str | None = None
    questionId: str | None = None
    text: str | None = None
    optionNumber: int | None = None
    imageUrl: str | None = None
    isCorrect: bool | None = None


class QuestionCreateRequest(QuestionBase):
    options: list[QuestionOptionCreate] | None = None

    @model_validator(mode="after")
    def validate_objective_options(self):
        objective_types = {
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.MULTIPLE_SELECT,
            QuestionType.TRUE_FALSE,
        }
        if self.questionType not in objective_types:
            return self

        options = self.options or []
        if not options:
            raise ValueError("Objective questions must include answer options")
        if self.questionType == QuestionType.TRUE_FALSE and len(options) != 2:
            raise ValueError("True/False questions must have exactly two options")

        correct_count = sum(option.isCorrect for option in options)
        if correct_count == 0:
            raise ValueError("Objective questions must include a correct option")
        if (
            self.questionType
            in (
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
            )
            and correct_count != 1
        ):
            raise ValueError(
                "Single-choice questions must have exactly one correct option"
            )
        return self


class QuestionUpdateRequest(BaseModel):
    id: str | None = None
    text: str | None = None
    marks: int | None = Field(default=None, gt=0)
    negativeMarks: float | None = Field(default=None, ge=0)
    questionNumber: int | None = Field(default=None, gt=0)
    questionType: QuestionType | None = None
    imageUrl: str | None = None
    wordLimit: int | None = Field(default=None, gt=0)
    explanation: str | None = None
    section: str | None = None
    options: list[QuestionOptionUpdate] | None = None


class QuestionResponse(QuestionBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
    options: list[QuestionOptionResponse] | None = None

    model_config = ConfigDict(from_attributes=True)
