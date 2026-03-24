# backend/tests/auth/conftest.py
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

# Import your cleanly separated dummy data!
from tests.dummy_data.users import TEST_USER_PAYLOAD, make_fake_user


# ── HTTP client (used by ALL tests) ──────────────────────────
@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


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


# ── Real DB fixtures (for integration tests only) ─────────────
@pytest_asyncio.fixture
async def real_db():
    """Creates a fresh Prisma client on the current event loop and
    monkey-patches the global singleton so the app's routes use it."""
    import app.core.database as db_module
    from prisma import Prisma

    original = db_module.prisma  # save the original
    fresh = Prisma()
    await fresh.connect()
    db_module.prisma = fresh  # patch the global

    yield fresh

    await fresh.disconnect()
    db_module.prisma = original  # restore


@pytest_asyncio.fixture
async def real_client(real_db):
    """HTTP client for integration tests (hits real DB).
    Depends on real_db so the global Prisma client is connected
    before any request hits the app's routes.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=False)
async def cleanup_real_user(real_db):
    """Deletes the test user from real DB after each integration test."""
    yield
    await real_db.user.delete_many(where={"email": TEST_USER_PAYLOAD["email"]})
