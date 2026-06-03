# backend/tests/school_class/conftest.py
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_class_db(mocker):
    patches = {
        "create_school_class": mocker.patch(
            "app.school_class.router.create_school_class",
            new_callable=AsyncMock,
        ),
        "get_school_class_by_id": mocker.patch(
            "app.school_class.router.get_school_class_by_id",
            new_callable=AsyncMock,
        ),
        "get_school_classes_by_school_id": mocker.patch(
            "app.school_class.router.get_school_classes_by_school_id",
            new_callable=AsyncMock,
        ),
        "get_student_by_user_id": mocker.patch(
            "app.school_class.router.get_student_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_students_by_class_id": mocker.patch(
            "app.school_class.router.get_students_by_class_id",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.school_class.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_principal_by_teacher_id": mocker.patch(
            "app.school_class.router.get_principal_by_teacher_id",
            new_callable=AsyncMock,
        ),
    }
    return patches
