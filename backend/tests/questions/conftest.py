# backend/tests/questions/conftest.py
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_questions_db(mocker):
    exam = MagicMock()
    exam.teacher = MagicMock(id="teacher_001", schoolId="school_001")
    patches = {
        "create_question": mocker.patch(
            "app.questions.router.crud.create_question",
            new_callable=AsyncMock,
        ),
        "get_question_by_id": mocker.patch(
            "app.questions.router.crud.get_question_by_id",
            new_callable=AsyncMock,
        ),
        "update_question": mocker.patch(
            "app.questions.router.crud.update_question",
            new_callable=AsyncMock,
        ),
        "delete_question": mocker.patch(
            "app.questions.router.crud.delete_question",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.questions.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_exam_by_id": mocker.patch(
            "app.questions.router.exam_crud.get_exam_by_id",
            new_callable=AsyncMock,
            return_value=exam,
        ),
    }
    return patches
