# backend/tests/dummy_data/exams.py
from datetime import datetime
from unittest.mock import MagicMock


def make_fake_exam(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}

    exam = MagicMock()
    exam.id = "clxfake_exam_001"
    exam.name = "Midterm Maths"
    exam.description = "Test description"
    exam.scheduledAt = datetime(2026, 1, 1)
    exam.duration = 60
    exam.maxMarks = 100
    exam.instructions = "Read carefully"
    exam.isPublished = False
    exam.subject = "MATHS"
    exam.type = "MIDTERM"
    exam.examCode = "EXM-A7B8C9"
    exam.isPublic = True
    exam.isResultsReleased = False
    exam.negativeMarking = False
    exam.negativeMarks = 0.0
    exam.teacherId = "clxfake_teacher_001"
    exam.createdAt = datetime(2026, 1, 1)
    exam.updatedAt = datetime(2026, 1, 1)
    exam.accessPassword = None
    exam.sections = []
    exam.questionCount = 0
    exam.questions = []

    # Setup nested objects
    exam.teacher = MagicMock()
    exam.teacher.id = "clxfake_teacher_001"
    exam.teacher.schoolId = "clxfake_school_001"
    exam.teacher.user = MagicMock()
    exam.teacher.user.name = "Teacher User"
    exam.teacher.school = MagicMock()
    exam.teacher.school.id = "clxfake_school_001"
    exam.teacher.school.name = "Test School"

    for k, v in overrides.items():
        setattr(exam, k, v)
    return exam


def make_fake_student_exam(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}

    se = MagicMock()
    se.id = "clxfake_se_001"
    se.studentId = "clxfake_student_001"
    se.examId = "clxfake_exam_001"
    se.marksObtained = 0.0
    se.startedAt = datetime(2026, 1, 1)
    se.submittedAt = None
    se.status = "IN_PROGRESS"
    se.isResultsReleased = False
    se.createdAt = datetime(2026, 1, 1)
    se.updatedAt = datetime(2026, 1, 1)
    se.answers = []

    for k, v in overrides.items():
        setattr(se, k, v)
    return se
