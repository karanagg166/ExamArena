# backend/tests/attempts/conftest.py
from unittest.mock import AsyncMock
import pytest

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
    }
    return patches
