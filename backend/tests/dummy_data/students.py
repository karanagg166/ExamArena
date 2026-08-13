# backend/tests/dummy_data/students.py
from datetime import datetime
from unittest.mock import MagicMock

from tests.dummy_data.users import make_fake_user


def make_fake_student(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}

    student = MagicMock()
    student.id = "clxfake_student_001"
    student.userId = "clxfake000000testuser"
    student.rollNo = "STU001"
    student.parentName = "Parent User"
    student.parentEmail = "parent@test.dev"
    student.fatherName = "John Doe"
    student.fatherEmail = "father@test.dev"
    student.fatherPhoneNo = "+1234567890"
    student.motherName = "Jane Doe"
    student.motherEmail = "mother@test.dev"
    student.motherPhoneNo = "+1234567891"
    student.guardianName = None
    student.guardianRelation = None
    student.guardianEmail = None
    student.guardianPhoneNo = None
    student.dateOfAdmission = datetime(2026, 1, 1)
    student.classId = "clxfake_class_001"
    student.className = "Class 10A"
    student.schoolId = "clxfake_school_001"
    student.schoolName = "Test School"
    student.createdAt = datetime(2026, 1, 1)
    student.updatedAt = datetime(2026, 1, 1)
    student.user = make_fake_user({"role": "STUDENT"})

    for k, v in overrides.items():
        setattr(student, k, v)
    return student
