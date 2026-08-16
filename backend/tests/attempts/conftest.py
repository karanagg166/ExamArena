# backend/tests/attempts/conftest.py
from unittest.mock import AsyncMock

import pytest

from tests.dummy_data.students import make_fake_student


@pytest.fixture
def mock_attempts_db(mocker):
    patches = {
        "start_exam_attempt": mocker.patch(
            "app.attempts.router.crud.start_exam_attempt",
            new_callable=AsyncMock,
        ),
        "get_attempt_by_id": mocker.patch(
            "app.attempts.router.crud.get_attempt_by_id",
            new_callable=AsyncMock,
        ),
        "submit_exam_attempt": mocker.patch(
            "app.attempts.router.crud.submit_exam_attempt",
            new_callable=AsyncMock,
        ),
        "get_student_by_user_id": mocker.patch(
            "app.attempts.router.get_student_by_user_id",
            new_callable=AsyncMock,
            return_value=make_fake_student(),
        ),
    }
    return patches
