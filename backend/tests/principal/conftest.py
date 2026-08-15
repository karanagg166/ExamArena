# backend/tests/principal/conftest.py
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_principal_db(mocker):
    patches = {
        "create_principal": mocker.patch(
            "app.principals.router.create_principal",
            new_callable=AsyncMock,
        ),
        "get_principal_by_teacher_id": mocker.patch(
            "app.principals.router.get_principal_by_teacher_id",
            new_callable=AsyncMock,
        ),
        "update_principal": mocker.patch(
            "app.principals.router.update_principal",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.principals.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "join_school": mocker.patch(
            "app.teachers.crud.join_school",
            new_callable=AsyncMock,
        ),
    }
    return patches
