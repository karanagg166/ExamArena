# backend/tests/sections/conftest.py
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_sections_db(mocker):
    patches = {
        "create_section": mocker.patch(
            "app.sections.router.crud.create_section",
            new_callable=AsyncMock,
        ),
        "get_sections_by_exam": mocker.patch(
            "app.sections.router.crud.get_sections_by_exam",
            new_callable=AsyncMock,
        ),
        "get_section_by_id": mocker.patch(
            "app.sections.router.crud.get_section_by_id",
            new_callable=AsyncMock,
        ),
        "update_section": mocker.patch(
            "app.sections.router.crud.update_section",
            new_callable=AsyncMock,
        ),
        "delete_section": mocker.patch(
            "app.sections.router.crud.delete_section",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.sections.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
    }
    return patches
