"""CLI runner to seed E2E fixtures for full-stack Playwright testing."""

import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from sqlalchemy import text

import app.core.database as db
from app.core.models import Base
from seeds.e2e_fullstack import seed_fullstack_e2e_fixtures


async def apply_migrations() -> None:
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    statements = [
        'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "examCode" VARCHAR;',
        'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "accessPassword" VARCHAR;',
        'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "isPublic" BOOLEAN NOT NULL DEFAULT TRUE;',
        'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "isResultsReleased" BOOLEAN NOT NULL DEFAULT FALSE;',
        'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "negativeMarking" BOOLEAN NOT NULL DEFAULT FALSE;',
        'ALTER TABLE "Exam" ADD COLUMN IF NOT EXISTS "negativeMarks" DOUBLE PRECISION NOT NULL DEFAULT 0.0;',
        'ALTER TABLE "ExamSection" ADD COLUMN IF NOT EXISTS "negativeMarking" BOOLEAN NOT NULL DEFAULT FALSE;',
        'ALTER TABLE "ExamSection" ADD COLUMN IF NOT EXISTS "negativeMarks" DOUBLE PRECISION NOT NULL DEFAULT 0.0;',
        'ALTER TABLE "ExamSection" ADD COLUMN IF NOT EXISTS "durationMinutes" INTEGER;',
        'ALTER TABLE "SchoolClass" ADD COLUMN IF NOT EXISTS "joinCode" VARCHAR;',
        'ALTER TABLE "SchoolClass" ADD COLUMN IF NOT EXISTS "nextRollNo" INTEGER NOT NULL DEFAULT 1;',
        'ALTER TABLE "Question" ADD COLUMN IF NOT EXISTS "referenceAnswer" TEXT;',
        'ALTER TABLE "Question" ADD COLUMN IF NOT EXISTS "gradingRubric" JSONB;',
        'ALTER TABLE "QuestionImport" ADD COLUMN IF NOT EXISTS "storageProvider" VARCHAR;',
        'ALTER TABLE "QuestionImport" ADD COLUMN IF NOT EXISTS "storageKey" VARCHAR;',
        'ALTER TABLE "QuestionImport" ADD COLUMN IF NOT EXISTS "storageUrl" VARCHAR;',
        'ALTER TABLE "QuestionImport" ADD COLUMN IF NOT EXISTS "storageResourceType" VARCHAR;',
        'ALTER TABLE "QuestionImport" ADD COLUMN IF NOT EXISTS "jobGeneration" INTEGER NOT NULL DEFAULT 1;',
        'ALTER TABLE "AnswerKeyImport" ADD COLUMN IF NOT EXISTS "storageProvider" VARCHAR NOT NULL DEFAULT \'LOCAL\';',
        'ALTER TABLE "AnswerKeyImport" ADD COLUMN IF NOT EXISTS "storageKey" VARCHAR;',
        'ALTER TABLE "AnswerKeyImport" ADD COLUMN IF NOT EXISTS "storageUrl" VARCHAR;',
        'ALTER TABLE "AnswerKeyImport" ADD COLUMN IF NOT EXISTS "storageResourceType" VARCHAR DEFAULT \'raw\';',
        'ALTER TABLE "AnswerKeyImport" ADD COLUMN IF NOT EXISTS "jobGeneration" INTEGER NOT NULL DEFAULT 1;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiSuggestedMarks" DOUBLE PRECISION;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiConfidence" VARCHAR;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiFeedback" TEXT;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiGradingBreakdown" JSONB;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiWarnings" JSONB;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiGradedAt" TIMESTAMPTZ;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "gradedBy" VARCHAR;',
        'ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "gradedAt" TIMESTAMPTZ;',
        'ALTER TABLE "StudentExam" ADD COLUMN IF NOT EXISTS "draftRevision" INTEGER NOT NULL DEFAULT 0;',
        'ALTER TABLE "StudentExam" ADD COLUMN IF NOT EXISTS "warningCount" INTEGER NOT NULL DEFAULT 0;',
    ]
    for stmt in statements:
        try:
            async with db.engine.begin() as conn:
                await conn.execute(text(stmt))
        except Exception as e:
            print(f"Migration notice: {e}")


async def main() -> None:
    await apply_migrations()
    async with db.AsyncSessionLocal() as session:
        try:
            await seed_fullstack_e2e_fixtures(session)
        except Exception as err:
            print(f"❌ Error during E2E seeding: {err}", flush=True)
            import traceback

            traceback.print_exc()
        finally:
            await db.close_db()


if __name__ == "__main__":
    asyncio.run(main())
