# backend/tests/auth/conftest.py
from unittest.mock import AsyncMock
import pytest
from tests.dummy_data.users import make_fake_user

# ── Fake user object ──────────────────────────────────────────
@pytest.fixture
def fake_user():
    """A ready-made fake User object."""
    return make_fake_user()


# ── Mock DB fixture ───────────────────────────────────────────
@pytest.fixture
def mock_db(mocker):
    """Patches all DB/crud calls so NO real database is touched."""
    patches = {
        "get_user_by_email": mocker.patch(
            "app.auth.router.get_user_by_email",
            new_callable=AsyncMock,
        ),
        "get_user_by_id": mocker.patch(
            "app.api.deps.get_user_by_id",
            new_callable=AsyncMock,
        ),
        "create_user": mocker.patch(
            "app.auth.router.crud_create_user",
            new_callable=AsyncMock,
        ),
        "verify_password": mocker.patch(
            "app.auth.router.verify_password",
        ),
        "create_access_token": mocker.patch(
            "app.auth.router.create_access_token",
            return_value="mocked.jwt.token",
        ),
        "verify_token": mocker.patch(
            "app.api.deps.verify_token",
        ),
    }
    return patches
