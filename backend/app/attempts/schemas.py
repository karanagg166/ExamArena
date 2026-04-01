from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel
from app.questions.schemas import QuestionType


# ─── Enums (match Prisma) ────────────────────────────────────────────────────

class AttemptStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"
    EXPIRED = "EXPIRED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"


class GradingStatus(StrEnum):
    PENDING = "PENDING"
    AUTO_GRADED = "AUTO_GRADED"
    MANUALLY_GRADED = "MANUALLY_GRADED"


class Correctness(StrEnum):
    FULLY_CORRECT = "FULLY_CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"


# ─── SelectedOption (Prisma: SelectedOption) ─────────────────────────────────

class SelectedOptionCreate(BaseModel):
    """Frontend sends only optionId — server links it to the answer"""
    optionId: str


class SelectedOptionResponse(BaseModel):
    id: str
    studentExamAnswerId: str
    optionId: str

    class Config:
        from_attributes = True


# ─── StudentExamAnswer (Prisma: StudentExamAnswer) ──────────────────────────

class StudentAnswerCreate(BaseModel):
    """When starting exam: create empty answer shells per question"""
    questionId: str
    questionType: QuestionType


class StudentAnswerUpdate(BaseModel):
    """When submitting: student fills in their answer for a question"""
    id: str
    textAnswer: str | None = None
    selectedOptions: list[SelectedOptionCreate] | None = None


class StudentAnswerResponse(BaseModel):
    """Full answer record returned from server"""
    id: str
    studentExamId: str
    questionId: str
    questionType: QuestionType
    textAnswer: str | None = None
    marksAwarded: int | None = None
    feedback: str | None = None
    isCorrect: Correctness | None = None
    gradingStatus: GradingStatus = GradingStatus.PENDING
    createdAt: datetime
    updatedAt: datetime
    selectedOptions: list[SelectedOptionResponse] | None = None

    class Config:
        from_attributes = True


# ─── StudentExam (Prisma: StudentExam) ───────────────────────────────────────

class StudentExamCreate(BaseModel):
    """When starting exam: frontend sends just examId
    Server injects studentId (from JWT), startedAt (now), status (IN_PROGRESS)"""
    examId: str


class StudentExamSubmit(BaseModel):
    """When submitting exam: send all answers at once"""
    id: str
    answers: list[StudentAnswerUpdate]


class StudentExamUpdate(BaseModel):
    """For teacher/admin grading or status updates"""
    id: str
    marksObtained: int | None = None
    status: AttemptStatus | None = None
    submittedAt: datetime | None = None


class StudentExamResponse(BaseModel):
    """Full attempt record returned from server"""
    id: str
    studentId: str
    examId: str
    marksObtained: int = 0
    startedAt: datetime
    submittedAt: datetime | None = None
    status: AttemptStatus = AttemptStatus.IN_PROGRESS
    answers: list[StudentAnswerResponse] | None = None

    class Config:
        from_attributes = True

