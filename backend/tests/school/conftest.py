# backend/tests/school/conftest.py
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_school_db(mocker):
    patches = {
        "get_school_by_user_id": mocker.patch(
            "app.school.router.crud.get_school_by_user_id",
            new_callable=AsyncMock,
        ),
        "create_school": mocker.patch(
            "app.school.router.crud.create_school",
            new_callable=AsyncMock,
        ),
        "update_school": mocker.patch(
            "app.school.router.crud.update_school",
            new_callable=AsyncMock,
        ),
        "delete_school": mocker.patch(
            "app.school.router.crud.delete_school",
            new_callable=AsyncMock,
        ),
        "get_schools": mocker.patch(
            "app.school.router.crud.get_schools",
            new_callable=AsyncMock,
        ),
        "get_school_by_name": mocker.patch(
            "app.school.router.crud.get_school_by_name",
            new_callable=AsyncMock,
        ),
        "get_school_by_code": mocker.patch(
            "app.school.router.crud.get_school_by_code",
            new_callable=AsyncMock,
        ),
        "get_school_by_id": mocker.patch(
            "app.school.router.crud.get_school_by_id",
            new_callable=AsyncMock,
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.school.router.get_teacher_by_user_id",
            new_callable=AsyncMock,
        ),
        "get_principal_by_teacher_id": mocker.patch(
            "app.school.router.get_principal_by_teacher_id",
            new_callable=AsyncMock,
        ),
        "create_principal": mocker.patch(
            "app.school.router.create_principal",
            new_callable=AsyncMock,
        ),
        "update_principal": mocker.patch(
            "app.school.router.update_principal",
            new_callable=AsyncMock,
        ),
        "get_school_classes_by_school_id": mocker.patch(
            "app.school.router.get_school_classes_by_school_id",
            new_callable=AsyncMock,
        ),
        "db": mocker.patch(
            "app.school.router.db",
        ),
    }
    return patches
