# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.api.deps import get_current_user
from app.core.models import User
from app.main import app
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
    """Initializes SQLAlchemy database and yields an AsyncSession."""
    import app.core.database as db_module

    await db_module.init_db()
    async with db_module.AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def real_client(real_db):
    """HTTP client for integration tests (hits real DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=False)
async def cleanup_real_user(real_db):
    """Deletes the test user from real DB after each integration test."""
    yield
    await real_db.execute(delete(User).where(User.email == TEST_USER_PAYLOAD["email"]))
    await real_db.commit()
