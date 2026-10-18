"""Tests for production import worker policy, degraded worker status, and fail-fast behavior."""

import io
import os
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import (
    AnswerKeyImport,
    AnswerKeyImportStatus,
    QuestionImport,
    QuestionImportStatus,
    Role,
)
from app.imports.worker import check_worker_availability
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "question_papers")


@pytest.mark.asyncio
async def test_worker_availability_diagnostics_reporting():
    """Verify check_worker_availability distinguishes Redis down vs Worker down vs Worker active."""
    # 1. Redis completely unreachable
    with patch("arq.create_pool", side_effect=ConnectionError("Cannot reach Redis")):
        status = await check_worker_availability()
        assert status["redis_configured"] is True
        assert status["redis_connected"] is False
        assert status["worker_available"] is False
        assert "Failed to connect to Redis" in status["detail"]

    # 2. Redis reachable, but no worker heartbeat / health check
    mock_pool_no_worker = AsyncMock()
    mock_pool_no_worker.get.return_value = None
    with patch("arq.create_pool", return_value=mock_pool_no_worker):
        status = await check_worker_availability()
        assert status["redis_configured"] is True
        assert status["redis_connected"] is True
        assert status["worker_available"] is False
        assert "no active arq worker detected" in status["detail"].lower()

    # 3. Redis reachable, active worker present
    mock_pool_active = AsyncMock()
    mock_pool_active.get.side_effect = lambda key: b"healthy" if key == "arq:worker:heartbeat" else None
    with patch("arq.create_pool", return_value=mock_pool_active):
        status = await check_worker_availability()
        assert status["redis_configured"] is True
        assert status["redis_connected"] is True
        assert status["worker_available"] is True
        assert "worker is active" in status["detail"].lower()


@pytest.mark.asyncio
async def test_question_import_fails_fast_when_worker_unavailable(
    auth_client_factory, db_session: AsyncSession, monkeypatch
):
    """In production (ALLOW_IN_PROCESS_IMPORT_FALLBACK=False), an absent worker produces HTTP 503,

    marks the record FAILED with error_category WORKER_UNAVAILABLE, and preserves the file.
    """
    monkeypatch.setattr(settings, "ALLOW_IN_PROCESS_IMPORT_FALLBACK", False)

    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_dp1@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-DP-1")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_dp1@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    valid_pdf_path = os.path.join(FIXTURES_DIR, "simple_mcq.pdf")
    with open(valid_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Mock Redis to simulate no active worker
    mock_pool = AsyncMock()
    mock_pool.get.return_value = None
    with patch("arq.create_pool", return_value=mock_pool):
        res = await client.post(
            f"/api/v1/exams/{exam.id}/question-imports",
            files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert res.status_code == 503
        data = res.json()["detail"]
        assert data["error"] == "WORKER_UNAVAILABLE"
        import_id = data["importId"]

    # Verify the database record exists, is marked FAILED with WORKER_UNAVAILABLE, and preserved
    stmt = select(QuestionImport).where(QuestionImport.id == import_id)
    record = (await db_session.execute(stmt)).scalar_one()
    assert record.status == QuestionImportStatus.FAILED
    assert record.errorCategory == "WORKER_UNAVAILABLE"
    assert "Worker unavailable" in (record.errorMessage or "")
    assert record.filePath is not None


@pytest.mark.asyncio
async def test_question_import_retry_succeeds_after_worker_recovery(
    auth_client_factory, db_session: AsyncSession, monkeypatch
):
    """Verify that retrying a failed WORKER_UNAVAILABLE import succeeds once the ARQ worker recovers."""
    monkeypatch.setattr(settings, "ALLOW_IN_PROCESS_IMPORT_FALLBACK", False)

    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_dp2@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-DP-2")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_dp2@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    # Initial failed import record
    failed_import = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="simple_mcq.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/simple_mcq.pdf",
        status=QuestionImportStatus.FAILED,
        errorCategory="WORKER_UNAVAILABLE",
        errorMessage="Worker unavailable: No persistent background worker is active.",
    )
    db_session.add(failed_import)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    # Simulate worker recovery: pool returns active heartbeat and enqueues job
    mock_job = AsyncMock()
    mock_job.job_id = "job-recovered-123"
    mock_pool_recovered = AsyncMock()
    mock_pool_recovered.get.return_value = b"healthy"
    mock_pool_recovered.enqueue_job.return_value = mock_job

    with patch("arq.create_pool", return_value=mock_pool_recovered):
        retry_res = await client.post(f"/api/v1/question-imports/{failed_import.id}/retry")
        assert retry_res.status_code == 200
        retry_data = retry_res.json()
        assert retry_data["status"] == "UPLOADED"
        assert retry_data["errorCategory"] is None
        mock_pool_recovered.enqueue_job.assert_awaited_once_with("run_import_job", failed_import.id, generation=2)


@pytest.mark.asyncio
async def test_answer_key_fails_fast_when_worker_unavailable(
    auth_client_factory, db_session: AsyncSession, monkeypatch
):
    """Verify answer key import also enforces persistent worker requirement and fails fast with 503."""
    monkeypatch.setattr(settings, "ALLOW_IN_PROCESS_IMPORT_FALLBACK", False)

    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_dp3@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-DP-3")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_dp3@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    valid_pdf_path = os.path.join(FIXTURES_DIR, "simple_mcq.pdf")
    with open(valid_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    mock_pool = AsyncMock()
    mock_pool.get.return_value = None
    with patch("arq.create_pool", return_value=mock_pool):
        res = await client.post(
            f"/api/v1/exams/{exam.id}/answer-key-imports",
            files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert res.status_code == 503
        data = res.json()["detail"]
        assert data["error"] == "WORKER_UNAVAILABLE"
        import_id = data["importId"]

    stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
    record = (await db_session.execute(stmt)).scalar_one()
    assert record.status == AnswerKeyImportStatus.FAILED
    assert record.errorCategory == "WORKER_UNAVAILABLE"
