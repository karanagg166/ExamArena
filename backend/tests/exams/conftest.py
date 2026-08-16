# backend/tests/exams/conftest.py
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_exams_db(mocker):
    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None

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
        "get_school_by_user_id": mocker.patch(
            "app.school.crud.get_school_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_exam_results": mocker.patch(
            "app.exams.router.crud.get_exam_results",
            new_callable=AsyncMock,
        ),
        "get_session": mocker.patch(
            "app.core.database.get_session",
            return_value=mock_session_ctx,
        ),
        "mock_session": mock_session,
    }
    return patches
