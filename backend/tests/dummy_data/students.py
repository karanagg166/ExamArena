# backend/tests/dummy_data/students.py
from unittest.mock import MagicMock
from datetime import datetime
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
    student.dateOfAdmission = datetime(2026, 1, 1)
    student.classId = "clxfake_class_001"
    student.schoolId = "clxfake_school_001"
    student.createdAt = datetime(2026, 1, 1)
    student.updatedAt = datetime(2026, 1, 1)
    student.user = make_fake_user({"role": "STUDENT"})
    
    for k, v in overrides.items():
        setattr(student, k, v)
    return student
