# backend/tests/teacher/conftest.py
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_teacher_db(mocker):
    patches = {
        "create_teacher": mocker.patch(
            "app.teachers.router.create_teacher",
            new_callable=AsyncMock,
        ),
        "get_all_qualifications": mocker.patch(
            "app.teachers.router.get_all_qualifications",
            new_callable=AsyncMock,
        ),
        "get_all_subjects": mocker.patch(
            "app.teachers.router.get_all_subjects",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.teachers.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_teachers": mocker.patch(
            "app.teachers.router.get_teachers",
            new_callable=AsyncMock,
        ),
        "join_school": mocker.patch(
            "app.teachers.router.join_school",
            new_callable=AsyncMock,
        ),
        "update_teacher": mocker.patch(
            "app.teachers.router.update_teacher",
            new_callable=AsyncMock,
        ),
        "crud_get_teacher_by_id": mocker.patch(
            "app.teachers.router.crud_get_teacher_by_id",
            new_callable=AsyncMock,
        ),
    }
    return patches
