from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "school_lookup"),
    [
        ("/api/v1/teacher-requests/request_1", "get_teacher_class_request_school_id"),
        (
            "/api/v1/teacher-requests/school-requests/request_1",
            "get_teacher_school_request_school_id",
        ),
    ],
)
async def test_principal_cannot_decide_request_for_another_school(
    client, override_auth, mocker, path, school_lookup
):
    override_auth(role="PRINCIPAL")
    mocker.patch(
        f"app.teacher_requests.router.crud.{school_lookup}",
        new=AsyncMock(return_value="target_school"),
    )
    mocker.patch(
        "app.school.crud.get_school_by_user_id",
        new=AsyncMock(return_value=None),
    )
    mocker.patch(
        "app.teacher_requests.router.get_teacher_by_user_id",
        new=AsyncMock(
            return_value=MagicMock(
                id="principal_teacher", schoolId="different_school", teaches=[]
            )
        ),
    )
    mocker.patch(
        "app.teacher_requests.router.get_principal_by_teacher_id",
        new=AsyncMock(return_value=MagicMock(schoolId="different_school")),
    )

    response = await client.patch(path, json={"status": "APPROVED"})

    assert response.status_code == 403
