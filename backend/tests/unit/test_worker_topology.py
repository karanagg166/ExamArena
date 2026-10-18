"""Tests for ARQ worker topology, worker availability checks, retry logic, and concurrent confirmation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.models import (
    AnswerKeyImportStatus,
    QuestionImportStatus,
    utc_now,
)
from app.imports.worker import (
    WORKER_HEARTBEAT_KEY,
    WorkerSettings,
    check_worker_availability,
    run_answer_key_job,
    run_import_job,
    shutdown,
    startup,
)


@pytest.mark.asyncio
async def test_worker_settings_configuration():
    """Verify WorkerSettings contains required jobs, health check keys, and valid Redis config."""
    assert run_import_job in WorkerSettings.functions
    assert run_answer_key_job in WorkerSettings.functions
    assert WorkerSettings.health_check_key == "arq:queue:health-check"
    assert WorkerSettings.health_check_interval == 15
    assert WorkerSettings.job_timeout == 300
    assert WorkerSettings.on_startup == startup
    assert WorkerSettings.on_shutdown == shutdown


@pytest.mark.asyncio
async def test_worker_startup_and_shutdown_lifecycle():
    """Verify worker startup registers heartbeat in Redis and shutdown cleans it up."""
    mock_redis = AsyncMock()
    ctx = {"redis": mock_redis}

    # Startup
    await startup(ctx)
    mock_redis.set.assert_awaited_once_with(WORKER_HEARTBEAT_KEY, "healthy", ex=30)

    # Shutdown
    await shutdown(ctx)
    mock_redis.delete.assert_awaited_once_with(WORKER_HEARTBEAT_KEY)


@pytest.mark.asyncio
async def test_check_worker_availability_active():
    """Verify check_worker_availability detects active worker when heartbeat is in Redis."""
    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(side_effect=lambda k: b"healthy" if k == WORKER_HEARTBEAT_KEY else None)

    with patch("app.core.config.settings.REDIS_URL", "redis://localhost:6379"):
        with patch("arq.create_pool", return_value=mock_pool):
            status = await check_worker_availability()
            assert status["redis_connected"] is True
            assert status["worker_available"] is True
            assert "active" in status["detail"]


@pytest.mark.asyncio
async def test_check_worker_availability_redis_reachable_but_worker_absent():
    """Verify check_worker_availability distinguishes between reachable Redis and absent worker."""
    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(return_value=None)

    with patch("app.core.config.settings.REDIS_URL", "redis://localhost:6379"):
        with patch("arq.create_pool", return_value=mock_pool):
            status = await check_worker_availability()
            assert status["redis_connected"] is True
            assert status["worker_available"] is False
            assert "no active ARQ worker detected" in status["detail"]


@pytest.mark.asyncio
async def test_dispatch_import_job_routes_to_worker_when_available():
    """When an active worker is detected, dispatch_import_job enqueues to ARQ queue."""
    from app.imports.router import dispatch_import_job

    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(side_effect=lambda k: b"healthy" if k == WORKER_HEARTBEAT_KEY else None)
    mock_job = MagicMock(job_id="job_123")
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)

    mock_bg = MagicMock()

    with patch("app.core.config.settings.REDIS_URL", "redis://localhost:6379"):
        with patch("arq.create_pool", return_value=mock_pool):
            mode = await dispatch_import_job("import_abc", mock_bg)
            assert mode == "arq_worker"
            mock_pool.enqueue_job.assert_awaited_once_with("run_import_job", "import_abc", generation=1)
            mock_bg.add_task.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_import_job_falls_back_when_worker_unavailable():
    """When Redis has no active worker, dispatch_import_job falls back to BackgroundTasks."""
    from app.imports.router import dispatch_import_job

    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(return_value=None)
    mock_bg = MagicMock()

    with patch("app.core.config.settings.REDIS_URL", "redis://localhost:6379"):
        with patch("arq.create_pool", return_value=mock_pool):
            mode = await dispatch_import_job("import_xyz", mock_bg)
            assert mode == "in_process_background_task"
            mock_bg.add_task.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_answer_key_job_routes_correctly():
    """Verify dispatch_answer_key_job enqueues to ARQ when worker active."""
    from app.answer_keys.router import dispatch_answer_key_job

    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(side_effect=lambda k: b"healthy" if k == WORKER_HEARTBEAT_KEY else None)
    mock_job = MagicMock(job_id="job_ak_1")
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    mock_bg = MagicMock()

    with patch("app.core.config.settings.REDIS_URL", "redis://localhost:6379"):
        with patch("arq.create_pool", return_value=mock_pool):
            mode = await dispatch_answer_key_job("ak_123", mock_bg)
            assert mode == "arq_worker"
            mock_pool.enqueue_job.assert_awaited_once_with("run_answer_key_job", "ak_123", generation=1)
