from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"


class QuestionBase(BaseModel):
    text: str
    marks: int
    questionNumber: int
    questionType: QuestionType
    imageUrl: str | None = None
    wordLimit: int | None = None
    explanation: str | None = None
    examId: str | None = None
    section: str

class QuestionOptionBase(BaseModel):
    text: str
    optionNumber: int
    imageUrl: str | None = None

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


class QuestionUpdateRequest(BaseModel):
    id: str | None = None
    text: str | None = None
    marks: int | None = None
    questionNumber: int | None = None
    questionType: QuestionType | None = None
    imageUrl: str | None = None
    wordLimit: int | None = None
    explanation: str | None = None
    section: str | None = None
    options: list[QuestionOptionUpdate] | None = None

class QuestionResponse(QuestionBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
    options: list[QuestionOptionResponse] | None = None

    model_config = ConfigDict(from_attributes=True)