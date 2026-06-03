# backend/tests/dummy_data/teachers.py
from unittest.mock import MagicMock
from datetime import datetime
from tests.dummy_data.users import make_fake_user

def make_fake_teacher(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}
    
    teacher = MagicMock()
    teacher.id = "clxfake_teacher_001"
    teacher.userId = "clxfake000000testuser"
    teacher.qualification = '["BACHELORS"]'  # String in Prisma (JSON serialized)
    teacher.qualifications = '["BACHELORS"]'
    teacher.experience = 5
    teacher.department = "Science"
    teacher.subjects = '["MATHS", "SCIENCE"]'  # String in Prisma (JSON serialized)
    teacher.schoolId = "clxfake_school_001"
    teacher.createdAt = datetime(2026, 1, 1)
    teacher.updatedAt = datetime(2026, 1, 1)
    teacher.user = make_fake_user({"role": "TEACHER"})
    
    for k, v in overrides.items():
        setattr(teacher, k, v)
    return teacher

def make_fake_principal(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}
        
    principal = MagicMock()
    principal.id = "clxfake_principal_001"
    principal.teacherId = "clxfake_teacher_001"
    principal.schoolId = "clxfake_school_001"
    principal.experience = 10
    principal.createdAt = datetime(2026, 1, 1)
    principal.updatedAt = datetime(2026, 1, 1)
    principal.teacher = make_fake_teacher()
    
    for k, v in overrides.items():
        setattr(principal, k, v)
    return principal
