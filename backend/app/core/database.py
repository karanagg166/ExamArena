import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.models import Base


def get_database_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/exam_arena",
    )
    # Fix scheme for SQLAlchemy asyncpg driver
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if "?" in url:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        if "sslmode" in query_params:
            ssl_val = query_params.pop("sslmode")[0]
            if ssl_val in ("require", "verify-ca", "verify-full", "prefer", "true"):
                query_params["ssl"] = ["require"]
        query_params.pop("channel_binding", None)
        new_query = urlencode(query_params, doseq=True)
        url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )

    return url


DATABASE_URL = get_database_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for standalone CRUD operations when no session is passed."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and handle column migrations."""
    from sqlalchemy import text

    from app.core.models import generate_exam_code

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(
                text('ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "examCode" VARCHAR;')
            )
            await conn.execute(
                text(
                    'CREATE UNIQUE INDEX IF NOT EXISTS exam_examcode_idx ON "Exam" ("examCode");'
                )
            )

            res = await conn.execute(
                text('SELECT id FROM "Exam" WHERE "examCode" IS NULL;')
            )
            rows = res.fetchall()
            for row in rows:
                code = generate_exam_code()
                await conn.execute(
                    text('UPDATE "Exam" SET "examCode" = :code WHERE id = :id;'),
                    {"code": code, "id": row.id},
                )
        except Exception as err:
            print("DB Migration notice (examCode):", err)


async def close_db() -> None:
    """Dispose engine connections."""
    await engine.dispose()
