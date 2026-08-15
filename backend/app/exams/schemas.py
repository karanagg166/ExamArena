from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.questions.schemas import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
)
from app.sections.schemas import SectionResponse


class ExamType(StrEnum):
    MIDTERM = "MIDTERM"
    FINAL = "FINAL"
    QUIZ = "QUIZ"
    ASSIGNMENT = "ASSIGNMENT"
    MOCK = "MOCK"


class Subject(StrEnum):
    MATHS = "MATHS"
    SCIENCE = "SCIENCE"
    HISTORY = "HISTORY"
    LITERATURE = "LITERATURE"
    ART = "ART"
    MUSIC = "MUSIC"
    PHYSICAL_EDUCATION = "PHYSICAL_EDUCATION"


class ExamBase(BaseModel):
    name: str
    description: str
    scheduledAt: datetime
    duration: int
    maxMarks: int
    instructions: str | None = None
    isPublished: bool = False
    isPublic: bool = True
    isResultsReleased: bool = False
    negativeMarking: bool = False
    negativeMarks: float = 0.0
    subject: Subject | None = None
    type: ExamType
    examCode: str | None = None
    accessPassword: str | None = None
    questionCount: int | None = None


class ExamCreateRequest(ExamBase):
    questions: list[QuestionCreateRequest] | None = None


class ExamUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    scheduledAt: datetime | None = None
    duration: int | None = None
    maxMarks: int | None = None
    instructions: str | None = None
    isPublished: bool | None = None
    isPublic: bool | None = None
    isResultsReleased: bool | None = None
    negativeMarking: bool | None = None
    negativeMarks: float | None = None
    subject: Subject | None = None
    type: ExamType | None = None
    examCode: str | None = None
    accessPassword: str | None = None
    questions: list[QuestionUpdateRequest] | None = None


class SchoolInfo(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class TeacherInfo(BaseModel):
    id: str
    user: UserInfo
    school: SchoolInfo | None = None
    model_config = ConfigDict(from_attributes=True)


class ExamResponse(ExamBase):
    id: str
    examCode: str
    createdAt: datetime
    updatedAt: datetime
    teacher: TeacherInfo | None = None
    sections: list[SectionResponse] | None = None
    questions: list[QuestionResponse] | None = None
    model_config = ConfigDict(from_attributes=True)


class StudentExamListItemResponse(ExamResponse):
    studentStatus: str | None = None
    attemptId: str | None = None
    model_config = ConfigDict(from_attributes=True)
