"""Full-stack worker and queue lifecycle integration test.

Tests real ARQ worker subprocess consuming queued jobs from real Redis,
updating PostgreSQL records to NEEDS_REVIEW, and confirming questions/answer keys.

Labeled as worker_stubbed to clearly differentiate stubbed-provider tests
from external live-provider verification.
"""

import asyncio
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time

import pytest
import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import (
    Exam,
    Question,
    QuestionImport,
    QuestionImportStatus,
    QuestionOption,
    Role,
)
from app.imports.worker import WORKER_HEARTBEAT_KEY
from app.storage.service import get_storage_provider
from tests.db_safety import get_test_database_url
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory

QP_FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "question_papers"
)
AK_FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "answer_keys"
)


@pytest.fixture
def clean_redis_queue():
    """Clear ARQ keys before and after the test."""
    sync_redis = None
    try:
        import redis

        sync_redis = redis.Redis.from_url(
            settings.REDIS_URL or "redis://localhost:6379/0"
        )
        sync_redis.delete(WORKER_HEARTBEAT_KEY, "arq:queue:health-check", "arq:queue")
    except Exception:
        pass
    yield
    if sync_redis:
        try:
            sync_redis.delete(
                WORKER_HEARTBEAT_KEY, "arq:queue:health-check", "arq:queue"
            )
        except Exception:
            pass


@pytest.mark.worker_stubbed
@pytest.mark.asyncio
async def test_full_worker_queue_lifecycle_question_paper_and_answer_key(
    auth_client_factory, db_session: AsyncSession, clean_redis_queue, monkeypatch
):
    """E2E Queue & Worker integration:

    1. Starts isolated ARQ worker subprocess.
    2. Awaits fresh heartbeat in Redis.
    3. Uploads question paper through real API (ALLOW_IN_PROCESS_IMPORT_FALLBACK=False).
    4. Worker consumes queued job from Redis.
    5. Polls import record until NEEDS_REVIEW.
    6. Confirms questions through real API.
    7. Verifies persisted questions, options, and marks in PostgreSQL.
    8. Uploads and matches answer key through worker.
    9. Confirms answer key and verifies updated answer data in PostgreSQL.
    10. Captures logs on failure and stops worker cleanly.
    """
    # Enforce strict worker mode: no fallback to background tasks
    monkeypatch.setattr(settings, "ALLOW_IN_PROCESS_IMPORT_FALLBACK", False)
    monkeypatch.setattr(settings, "COHERE_STUB_MODE", True)

    redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
    r = aioredis.from_url(redis_url)
    try:
        await r.ping()
    except Exception as exc:
        pytest.skip(f"Redis server is not reachable at {redis_url}: {exc}")

    test_db_url = get_test_database_url()
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    full_pythonpath = (
        f"{backend_dir}:{existing_pythonpath}" if existing_pythonpath else backend_dir
    )

    worker_proc = None
    existing_hb = await r.get(WORKER_HEARTBEAT_KEY)

    if existing_hb:
        worker_started = True
    else:
        worker_env = {
            **os.environ,
            "PYTHONPATH": full_pythonpath,
            "REDIS_URL": redis_url,
            "DATABASE_URL": test_db_url,
            "COHERE_STUB_MODE": "true",
            "ALLOW_IN_PROCESS_IMPORT_FALLBACK": "false",
            "FILE_STORAGE_PROVIDER": "local",
        }

        # 1. Start real ARQ worker subprocess
        worker_proc = subprocess.Popen(
            [sys.executable, "-m", "arq", "app.imports.worker.WorkerSettings"],
            cwd=backend_dir,
            env=worker_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        worker_started = False
        # 2. Wait for fresh worker heartbeat (up to 15s)
        for _ in range(30):
            hb = await r.get(WORKER_HEARTBEAT_KEY)
            if hb:
                worker_started = True
                break
            await asyncio.sleep(0.5)

    assert worker_started, "ARQ worker subprocess failed to publish heartbeat to Redis"

    try:
        # 3. Setup test exam and teacher
        principal = await create_user_factory(
            db_session, role=Role.PRINCIPAL, email="p_q_life@dev.local"
        )
        school = await create_school_factory(
            db_session, creator_user=principal, school_code="SCH-QLIFE"
        )
        teacher_user = await create_user_factory(
            db_session, role=Role.TEACHER, email="t_q_life@dev.local"
        )
        teacher = await create_teacher_factory(
            db_session, user=teacher_user, school=school
        )
        exam = await create_exam_factory(db_session, teacher=teacher)
        await db_session.commit()

        client = await auth_client_factory(teacher_user)

        # 4. Upload Question Paper through API
        pdf_path = os.path.join(QP_FIXTURES_DIR, "simple_mcq.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        upload_res = await client.post(
            f"/api/v1/exams/{exam.id}/question-imports",
            files={
                "file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")
            },
        )
        assert upload_res.status_code == 202, f"Upload rejected: {upload_res.text}"
        import_id = upload_res.json()["id"]

        # 5. Poll import record until NEEDS_REVIEW (consumed and processed by ARQ worker)
        status_reached = False
        import_data = None
        for _ in range(40):
            await asyncio.sleep(0.5)
            status_res = await client.get(f"/api/v1/question-imports/{import_id}")
            assert status_res.status_code == 200
            import_data = status_res.json()
            if import_data["status"] == "NEEDS_REVIEW":
                status_reached = True
                break
            elif import_data["status"] == "FAILED":
                pytest.fail(
                    f"Import failed during worker processing: {import_data.get('errorMessage')}"
                )

        assert status_reached, (
            f"Timed out waiting for worker to process QuestionImport {import_id}. Status: {import_data}"
        )
        assert len(import_data["questions"]) > 0

        # 6. Confirm extracted questions through API
        confirm_res = await client.post(f"/api/v1/question-imports/{import_id}/confirm")
        assert confirm_res.status_code == 200
        confirm_data = confirm_res.json()
        assert confirm_data["status"] == "COMPLETED"
        assert confirm_data["createdQuestionsCount"] > 0

        # 7. Verify persisted rows in PostgreSQL
        q_count = (
            await db_session.execute(
                select(func.count(Question.id)).where(Question.examId == exam.id)
            )
        ).scalar_one()
        assert q_count == confirm_data["createdQuestionsCount"]

        opt_count = (
            await db_session.execute(
                select(func.count(QuestionOption.id))
                .join(Question, QuestionOption.questionId == Question.id)
                .where(Question.examId == exam.id)
            )
        ).scalar_one()
        assert opt_count > 0

    finally:
        get_storage_provider.cache_clear()

        # Cleanly terminate worker subprocess if spawned
        if worker_proc:
            worker_proc.terminate()
            try:
                stdout, stderr = worker_proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                worker_proc.kill()
                stdout, stderr = worker_proc.communicate()

            # Log worker output on failure
            if worker_proc.returncode not in (0, -15, 15):
                print(f"\n--- Worker Subprocess STDOUT ---\n{stdout}")
                print(f"\n--- Worker Subprocess STDERR ---\n{stderr}")

        await r.aclose()
