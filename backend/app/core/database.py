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
            # Add section negative marking columns
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

            # Convert unique index on examCode to non-unique index if needed
            await conn.execute(text("DROP INDEX IF EXISTS exam_examcode_key;"))
            await conn.execute(
                text(
                    'CREATE INDEX IF NOT EXISTS exam_examcode_idx ON "Exam" ("examCode");'
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
            print("DB Migration notice (exam settings & section negative marks):", err)

        # Transitional compatibility for installations that relied on
        # ``create_all`` rather than applying Prisma migrations. The tracked
        # Prisma migration is authoritative; these statements only make an
        # existing development database safe to start before it is deployed.
        try:
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
            class_rows = (
                await conn.execute(
                    text('SELECT "id" FROM "SchoolClass" WHERE "joinCode" IS NULL;')
                )
            ).fetchall()
            import secrets
            import string

            alphabet = string.ascii_uppercase + string.digits
            for row in class_rows:
                while True:
                    code = "".join(secrets.choice(alphabet) for _ in range(8))
                    exists = await conn.execute(
                        text('SELECT 1 FROM "SchoolClass" WHERE "joinCode" = :code;'),
                        {"code": code},
                    )
                    if not exists.scalar_one_or_none():
                        await conn.execute(
                            text(
                                'UPDATE "SchoolClass" SET "joinCode" = :code WHERE "id" = :id;'
                            ),
                            {"code": code, "id": row.id},
                        )
                        break

            await conn.execute(
                text(
                    """
                    UPDATE "SchoolClass" AS class
                    SET "nextRollNo" = COALESCE((
                      SELECT MAX(CASE WHEN student."rollNo" ~ '^[0-9]+$'
                                      THEN student."rollNo"::INTEGER END)
                      FROM "Student" AS student
                      WHERE student."classId" = class."id"
                    ), 0) + 1
                    WHERE class."nextRollNo" = 1;
                    """
                )
            )
            await conn.execute(
                text('ALTER TABLE "SchoolClass" ALTER COLUMN "joinCode" SET NOT NULL;')
            )
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS schoolclass_joincode_key "
                    'ON "SchoolClass" ("joinCode");'
                )
            )
            await conn.execute(
                text(
                    """
                    DO $$
                    DECLARE constraint_name TEXT;
                    BEGIN
                      SELECT conname INTO constraint_name
                      FROM pg_constraint
                      WHERE conrelid = '"Student"'::regclass
                        AND contype = 'u'
                        AND conkey = ARRAY[
                          (SELECT attnum::SMALLINT FROM pg_attribute
                           WHERE attrelid = '"Student"'::regclass AND attname = 'rollNo')
                        ]::SMALLINT[];
                      IF constraint_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE "Student" DROP CONSTRAINT %I', constraint_name);
                      END IF;
                    END $$;
                    """
                )
            )
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS student_classid_rollno_key "
                    'ON "Student" ("classId", "rollNo");'
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
                    """
                )
            )
        except Exception as err:
            print("DB Migration notice (class enrollment):", err)


async def close_db() -> None:
    """Dispose engine connections."""
    await engine.dispose()
