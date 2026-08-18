"""Pytest configuration, fixtures, and isolated test database management."""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.core.database as app_db
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.models import Base
from app.core.security import create_access_token
from app.main import app
from tests.db_safety import get_test_database_url, verify_database_safety
from tests.dummy_data.users import make_fake_user

# ── 1. Configure and verify test database ─────────────────────────────────────
TEST_DB_URL = get_test_database_url()
verify_database_safety(TEST_DB_URL)

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_test_db() -> None:
    """Ensure test database exists, create schema, and apply schema migrations."""
    import urllib.parse
    import asyncpg

    clean_url = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    parsed = urllib.parse.urlparse(clean_url)
    user = parsed.username or "postgres"
    password = parsed.password or "postgres"
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    test_db_name = parsed.path.lstrip("/") or "exam_arena_test"

    for maintenance_db in ["postgres", "exam_arena"]:
        try:
            sys_conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=maintenance_db,
            )
            exists = await sys_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", test_db_name
            )
            if not exists:
                await sys_conn.execute(f'CREATE DATABASE "{test_db_name}"')
            await sys_conn.close()
            break
        except Exception:
            pass

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Apply columns migrations
        try:
            await conn.execute(
                text('ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "examCode" VARCHAR;')
            )
            await conn.execute(
                text(
                    'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "accessPassword" VARCHAR;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "isPublic" BOOLEAN NOT NULL DEFAULT TRUE;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "isResultsReleased" BOOLEAN NOT NULL DEFAULT FALSE;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "negativeMarking" BOOLEAN NOT NULL DEFAULT FALSE;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "negativeMarks" DOUBLE PRECISION NOT NULL DEFAULT 0.0;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "ExamSection" ADD COLUMN IF NOT EXISTS "negativeMarking" BOOLEAN NOT NULL DEFAULT FALSE;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "ExamSection" ADD COLUMN IF NOT EXISTS "negativeMarks" DOUBLE PRECISION NOT NULL DEFAULT 0.0;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "ExamSection" ADD COLUMN IF NOT EXISTS "durationMinutes" INTEGER;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "SchoolClass" ADD COLUMN IF NOT EXISTS "joinCode" VARCHAR;'
                )
            )
            await conn.execute(
                text(
                    'ALTER TABLE "SchoolClass" ADD COLUMN IF NOT EXISTS "nextRollNo" INTEGER NOT NULL DEFAULT 1;'
                )
            )
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS "TeacherSchoolJoinRequest" (
                        "id" VARCHAR PRIMARY KEY,
                        "teacherId" VARCHAR NOT NULL REFERENCES "Teacher"("id") ON DELETE CASCADE,
                        "schoolId" VARCHAR NOT NULL REFERENCES "School"("id") ON DELETE CASCADE,
                        "status" VARCHAR NOT NULL DEFAULT 'PENDING',
                        "requestedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        "decidedAt" TIMESTAMPTZ,
                        "decidedBy" VARCHAR,
                        CONSTRAINT "teacherschooljoinrequest_teacherid_schoolid_key" UNIQUE ("teacherId", "schoolId")
                    );
                    CREATE INDEX IF NOT EXISTS "teacherschooljoinrequest_schoolid_idx" ON "TeacherSchoolJoinRequest" ("schoolId");
                    CREATE INDEX IF NOT EXISTS "teacherschooljoinrequest_teacherid_idx" ON "TeacherSchoolJoinRequest" ("teacherId");
                    CREATE TABLE IF NOT EXISTS "AuditLog" (
                        "id" VARCHAR PRIMARY KEY,
                        "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        "actorId" VARCHAR,
                        "actorEmail" VARCHAR,
                        "actorRole" VARCHAR,
                        "action" VARCHAR NOT NULL,
                        "resourceType" VARCHAR NOT NULL,
                        "resourceId" VARCHAR,
                        "status" VARCHAR NOT NULL DEFAULT 'SUCCESS',
                        "requestId" VARCHAR,
                        "ipAddress" VARCHAR,
                        "userAgent" VARCHAR,
                        "metadata" JSON
                    );
                    CREATE INDEX IF NOT EXISTS "auditlog_timestamp_idx" ON "AuditLog" ("timestamp");
                    CREATE INDEX IF NOT EXISTS "auditlog_actorid_idx" ON "AuditLog" ("actorId");
                    CREATE INDEX IF NOT EXISTS "auditlog_action_idx" ON "AuditLog" ("action");
                    CREATE INDEX IF NOT EXISTS "auditlog_resourcetype_idx" ON "AuditLog" ("resourceType");
                    CREATE INDEX IF NOT EXISTS "auditlog_resourceid_idx" ON "AuditLog" ("resourceId");
                    CREATE INDEX IF NOT EXISTS "auditlog_requestid_idx" ON "AuditLog" ("requestId");
                    """
                )
            )
        except Exception:
            pass


# ── 2. Session and Clean DB Fixtures ──────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def setup_test_db_infrastructure():
    """Session-level fixture to initialize the test database once."""
    verify_database_safety(TEST_DB_URL)
    asyncio.run(init_test_db())
    app_db.engine = test_engine
    app_db.AsyncSessionLocal = TestAsyncSessionLocal
    yield
    asyncio.run(test_engine.dispose())


@pytest.fixture(autouse=True)
def override_db_dependency_globally():
    """Ensure FastAPI dependency get_db always resolves to the isolated test database."""
    async def _override_get_db():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


async def truncate_all_tables():
    """Truncate all tables for complete isolation."""
    async with test_engine.begin() as conn:
        try:
            await conn.execute(
                text(
                    """
                    TRUNCATE TABLE
                        "AuditLog",
                        "SelectedOption",
                        "StudentExamAnswer",
                        "StudentExam",
                        "QuestionOption",
                        "Question",
                        "ExamSection",
                        "Exam",
                        "ClassJoinRequest",
                        "TeacherClassJoinRequest",
                        "TeacherSchoolJoinRequest",
                        "TeacherClass",
                        "Principal",
                        "Student",
                        "Teacher",
                        "SchoolClass",
                        "School",
                        "Notification",
                        "User"
                    CASCADE;
                    """
                )
            )
        except Exception:
            pass


@pytest_asyncio.fixture
async def clean_db():
    """Clean all tables before and after test."""
    await truncate_all_tables()
    yield
    await truncate_all_tables()


@pytest_asyncio.fixture
async def db_session(clean_db) -> AsyncGenerator[AsyncSession, None]:
    """Yield an active isolated AsyncSession for database operations."""
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()


# ── 3. FastAPI Client Fixtures ───────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(clean_db) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired directly to the FastAPI app."""

    async def override_get_db():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def override_auth():
    """Helper to override get_current_user in unit tests."""

    def _override(role="STUDENT", user_overrides=None):
        if user_overrides is None:
            user_overrides = {}
        user_overrides["role"] = role
        user = make_fake_user(user_overrides)
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _override
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def auth_client_factory():
    """Factory fixture returning an authenticated AsyncClient with cookie set."""
    created_clients = []

    async def _make_client(user) -> AsyncClient:
        token = create_access_token(user.id)
        ac = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            cookies={"access_token": token},
        )
        created_clients.append(ac)
        return ac

    yield _make_client
    for ac in created_clients:
        await ac.aclose()


# ── 4. Legacy compatibility fixtures ──────────────────────────────────────────


@pytest_asyncio.fixture
async def real_db(db_session):
    yield db_session


@pytest_asyncio.fixture
async def real_client(client):
    yield client
