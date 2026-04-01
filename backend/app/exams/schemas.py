from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.questions.schemas import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
)


class ExamType(StrEnum):
    MIDTERM = "MIDTERM"
    FINAL="FINAL"
    QUIZ="QUIZ"
    ASSIGNMENT="ASSIGNMENT"
    MOCK="MOCK"   

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
    subject: Subject | None = None
    type: ExamType
    teacherId: str | None = None

class ExamCreateRequest(ExamBase):
    questions: list[QuestionCreateRequest] | None = None
    pass

class ExamUpdateRequest(BaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    scheduledAt: datetime | None = None
    duration: int | None = None
    maxMarks: int | None = None
    instructions: str | None = None
    isPublished: bool | None = None
    subject: Subject | None = None
    type: ExamType | None = None
    teacherId: str | None = None
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
    createdAt: datetime
    updatedAt: datetime
    teacher: TeacherInfo | None = None
    questions: list[QuestionResponse] | None = None
    model_config = ConfigDict(from_attributes=True)