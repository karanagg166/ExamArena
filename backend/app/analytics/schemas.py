"""Pydantic schemas and contracts for teacher results and analytics."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.attempts.schemas import ExamScoreboardItem


class PerformanceBracket(str, Enum):
    ALL = "ALL"
    PASSED = "PASSED"
    FAILED = "FAILED"
    DISTINCTION = "DISTINCTION"


class AnalyticsSortBy(str, Enum):
    RANK = "rank"
    SCORE = "score"
    PERCENTAGE = "percentage"
    NAME = "name"
    ROLL_NO = "rollNo"
    SUBMITTED_AT = "submittedAt"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class TeacherResultsOverviewResponse(BaseModel):
    """Aggregate high-level metric overview for authorized teacher or principal."""

    totalExams: int
    totalAttempts: int
    gradedAttempts: int
    pendingGradingAttempts: int
    averagePercentage: float
    classes: int

    model_config = ConfigDict(from_attributes=True)


class ExamGradingWorkloadSummary(BaseModel):
    """Grading workload metrics for subjective questions in an exam."""

    totalSubjectiveAnswers: int = 0
    pendingSubjectiveCount: int = 0
    aiSuggestionsReadyCount: int = 0
    teacherGradedSubjectiveCount: int = 0

    model_config = ConfigDict(from_attributes=True)


class ClassExamPerformanceItem(BaseModel):
    """Per-exam performance breakdown within a class analytics context."""

    examId: str
    examTitle: str
    examCode: str
    subject: str
    maxMarks: int
    studentsAttempted: int
    averagePercentage: float
    highestPercentage: float
    lowestPercentage: float
    passRate: float
    pendingSubjectiveCount: int = 0
    aiSuggestionsReadyCount: int = 0
    teacherGradedSubjectiveCount: int = 0
    isResultsReleased: bool = False

    model_config = ConfigDict(from_attributes=True)


class ClassAnalyticsSummary(BaseModel):
    """High-level class statistics across all exams."""

    classId: str
    className: str
    year: str
    section: str
    totalStudents: int
    totalExams: int
    totalAttempts: int
    gradedAttempts: int
    pendingGradingAttempts: int
    classAveragePercentage: float
    highestPercentage: float
    lowestPercentage: float
    passRate: float
    gradingCompletionRate: float

    model_config = ConfigDict(from_attributes=True)


class ClassResultsResponse(BaseModel):
    """Complete class analytics response with summary and exam breakdown."""

    summary: ClassAnalyticsSummary
    exams: list[ClassExamPerformanceItem]

    model_config = ConfigDict(from_attributes=True)


class ClassLeaderboardEntry(BaseModel):
    """Row in normalized class-wide aggregate ranking across finalized exams."""

    rank: int
    studentId: str
    studentName: str
    rollNo: str
    examsAttempted: int
    finalizedExamsCount: int
    averagePercentage: float
    passedExamsCount: int

    model_config = ConfigDict(from_attributes=True)


class ClassLeaderboardResponse(BaseModel):
    """Leaderboard ranking students across multiple exams normalized by percentage."""

    classId: str
    className: str
    totalStudents: int
    leaderboard: list[ClassLeaderboardEntry]
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)


class StudentPerformanceSummary(BaseModel):
    """Aggregate performance summary for a specific student across exams."""

    studentId: str
    studentName: str
    rollNo: str
    totalExams: int
    averagePercentage: float
    highestPercentage: float
    lowestPercentage: float
    passed: int
    failed: int
    pendingSubjectiveGradingExams: int = 0

    model_config = ConfigDict(from_attributes=True)


class StudentResultHistoryItem(BaseModel):
    """Single exam attempt record in student history."""

    attemptId: str
    examId: str
    examTitle: str
    examCode: str
    subject: str
    date: datetime | None = None
    marksObtained: float
    maxMarks: int
    percentage: float
    status: str
    isFinalized: bool
    classId: str | None = None
    className: str | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentResultsResponse(BaseModel):
    """Authorized teacher response for student performance and history."""

    summary: StudentPerformanceSummary
    history: list[StudentResultHistoryItem]
    limit: int
    offset: int
    totalCount: int

    model_config = ConfigDict(from_attributes=True)


class ExamAnalyticsDetailResponse(BaseModel):
    """Detailed exam analytics including workload and paginated leaderboard."""

    examId: str
    examTitle: str
    examCode: str
    subject: str
    maxMarks: int
    totalAttempts: int
    gradedAttempts: int
    pendingGradingAttempts: int
    averagePercentage: float
    highestPercentage: float
    lowestPercentage: float
    passRate: float
    workload: ExamGradingWorkloadSummary
    leaderboard: list[ExamScoreboardItem]
    totalCount: int
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)
