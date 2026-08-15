from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_join_request_db(mocker):
    return {
        "get_student_by_user_id": mocker.patch(
            "app.join_requests.router.get_student_by_user_id", new_callable=AsyncMock
        ),
        "get_class_by_join_code": mocker.patch(
            "app.join_requests.router.get_class_by_join_code", new_callable=AsyncMock
        ),
        "create_or_reopen_join_request": mocker.patch(
            "app.join_requests.router.create_or_reopen_join_request",
            new_callable=AsyncMock,
        ),
        "get_join_requests_for_user": mocker.patch(
            "app.join_requests.router.get_join_requests_for_user",
            new_callable=AsyncMock,
        ),
        "get_school_class_by_id": mocker.patch(
            "app.join_requests.router.get_school_class_by_id", new_callable=AsyncMock
        ),
        "get_join_requests_for_class": mocker.patch(
            "app.join_requests.router.get_join_requests_for_class",
            new_callable=AsyncMock,
        ),
        "get_join_request_by_id": mocker.patch(
            "app.join_requests.router.get_join_request_by_id", new_callable=AsyncMock
        ),
        "get_teacher_by_user_id": mocker.patch(
            "app.join_requests.router.get_teacher_by_user_id", new_callable=AsyncMock
        ),
        "get_principal_by_teacher_id": mocker.patch(
            "app.join_requests.router.get_principal_by_teacher_id",
            new_callable=AsyncMock,
        ),
        "decide_join_request": mocker.patch(
            "app.join_requests.router.decide_join_request", new_callable=AsyncMock
        ),
    }
