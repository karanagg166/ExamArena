# backend/tests/conftest.py
import pytest
import pytest_asyncio
from unittest.mock import MagicMock
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.deps import get_current_user
from tests.dummy_data.users import TEST_USER_PAYLOAD, make_fake_user

@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

@pytest.fixture
def override_auth():
    """
    Returns a helper to override authenticated user role.
    Usage:
        fake_user = override_auth(role="TEACHER")
    """
    def _override(role="STUDENT", user_overrides=None):
        if user_overrides is None:
            user_overrides = {}
        user_overrides["role"] = role
        user = make_fake_user(user_overrides)
        app.dependency_overrides[get_current_user] = lambda: user
        return user
        
    yield _override
    app.dependency_overrides.clear()

# ── Real DB fixtures (for integration tests only) ─────────────
@pytest_asyncio.fixture
async def real_db():
    """Creates a fresh Prisma client on the current event loop and
    monkey-patches the global singleton so the app's routes use it."""
    import app.core.database as db_module
    from app.generated.prisma import Prisma

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
