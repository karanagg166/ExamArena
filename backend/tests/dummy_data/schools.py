# backend/tests/dummy_data/schools.py
from unittest.mock import MagicMock
from datetime import datetime

def make_fake_school(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}
        
    school = MagicMock()
    school.id = "clxfake_school_001"
    school.name = "Test School"
    school.createdBy = "clxfake000000testuser"
    school.address = "123 Test St"
    school.city = "Mumbai"
    school.state = "Maharashtra"
    school.country = "India"
    school.pincode = "400001"
    school.schoolCode = "TST001"
    school.type = "PUBLIC"  # SchoolType enum
    school.email = "school@test.dev"
    school.website = "https://test.school"
    school.createdAt = datetime(2026, 1, 1)
    school.updatedAt = datetime(2026, 1, 1)
    school.principalName = None
    school.principals = []
    
    for k, v in overrides.items():
        setattr(school, k, v)
    return school

def make_fake_school_class(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}
        
    sc = MagicMock()
    sc.id = "clxfake_class_001"
    sc.name = "12th - A"
    sc.year = "12th"
    sc.section = "A"
    sc.schoolId = "clxfake_school_001"
    sc.teacherId = None
    sc.createdAt = datetime(2026, 1, 1)
    sc.updatedAt = datetime(2026, 1, 1)
    
    for k, v in overrides.items():
        setattr(sc, k, v)
    return sc
