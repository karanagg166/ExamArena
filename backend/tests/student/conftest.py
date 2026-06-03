# backend/tests/student/conftest.py
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_student_db(mocker):
    patches = {
        "create_student": mocker.patch(
            "app.students.router.create_student",
            new_callable=AsyncMock,
        ),
        "get_student_by_id": mocker.patch(
            "app.students.router.get_student_by_id",
            new_callable=AsyncMock,
        ),
        "get_student_by_user_id": mocker.patch(
            "app.students.router.get_student_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_students": mocker.patch(
            "app.students.router.get_students",
            new_callable=AsyncMock,
        ),
        "update_student": mocker.patch(
            "app.students.router.update_student",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.students.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_principal_by_teacher_id": mocker.patch(
            "app.students.router.get_principal_by_teacher_id",
            new_callable=AsyncMock,
        ),
    }
    return patches
