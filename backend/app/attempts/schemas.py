from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, model_validator

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
    id: str | None = None
    studentExamAnswerId: str | None = None
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
    marksAwarded: float | None = None
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
    """When starting exam: frontend sends examId and optional examCode"""

    examId: str
    examCode: str | None = None


class StudentExamSubmit(BaseModel):
    """When submitting exam: send all answers at once"""

    id: str
    answers: list[StudentAnswerUpdate]

    @model_validator(mode="after")
    def validate_unique_answer_references(self):
        answer_ids = [answer.id for answer in self.answers]
        if len(answer_ids) != len(set(answer_ids)):
            raise ValueError("Each answer may only be submitted once")
        for answer in self.answers:
            option_ids = [item.optionId for item in answer.selectedOptions or []]
            if len(option_ids) != len(set(option_ids)):
                raise ValueError("Each option may only be selected once per answer")
        return self


class StudentExamUpdate(BaseModel):
    """For teacher/admin grading or status updates"""

    id: str
    marksObtained: float | None = None
    status: AttemptStatus | None = None
    submittedAt: datetime | None = None


class StudentExamResponse(BaseModel):
    """Full attempt record returned from server"""

    id: str
    studentId: str
    examId: str
    marksObtained: float = 0.0
    startedAt: datetime
    submittedAt: datetime | None = None
    status: AttemptStatus = AttemptStatus.IN_PROGRESS
    isResultsReleased: bool = False
    answers: list[StudentAnswerResponse] | None = None

    class Config:
        from_attributes = True


class StudentExamHistoryItem(BaseModel):
    """Row in a student's complete exam history table for staff viewing."""

    id: str
    examId: str
    examTitle: str
    examCode: str
    subject: str | None = None
    examType: str
    scheduledAt: datetime
    submittedAt: datetime | None = None
    status: str
    marksObtained: float
    maxMarks: int
    percentage: float
    isResultsReleased: bool

    class Config:
        from_attributes = True


class ExamScoreboardItem(BaseModel):
    """Row in an exam's results scoreboard leaderboard."""

    rank: int
    studentId: str
    studentName: str
    rollNo: str
    marksObtained: float
    maxMarks: int
    percentage: float
    status: str
    startedAt: datetime | None = None
    submittedAt: datetime | None = None

    class Config:
        from_attributes = True
