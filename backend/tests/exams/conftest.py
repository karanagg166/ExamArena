# backend/tests/exams/conftest.py
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_exams_db(mocker):
    patches = {
        "create_exam": mocker.patch(
            "app.exams.router.crud.create_exam",
            new_callable=AsyncMock,
        ),
        "get_exams_by_teacher": mocker.patch(
            "app.exams.router.crud.get_exams_by_teacher",
            new_callable=AsyncMock,
        ),
        "get_published_exams": mocker.patch(
            "app.exams.router.crud.get_published_exams",
            new_callable=AsyncMock,
        ),
        "get_published_exams_for_student": mocker.patch(
            "app.exams.router.crud.get_published_exams_for_student",
            new_callable=AsyncMock,
        ),
        "get_exam_by_id": mocker.patch(
            "app.exams.router.crud.get_exam_by_id",
            new_callable=AsyncMock,
        ),
        "update_exam": mocker.patch(
            "app.exams.router.crud.update_exam",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.exams.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "student_crud_get_student_by_user_id": mocker.patch(
            "app.students.crud.get_student_by_user_id",
            new_callable=AsyncMock,
        ),
        "prisma": mocker.patch(
            "app.core.database.prisma",
        ),
    }
    return patches
