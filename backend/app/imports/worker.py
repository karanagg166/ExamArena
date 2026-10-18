"""Worker settings and ARQ job definitions for question paper and answer key imports."""

import logging
from typing import Any

from arq.connections import RedisSettings

from app.answer_keys.service import process_answer_key_import
from app.core.config import settings
from app.imports.service import process_question_import

logger = logging.getLogger(__name__)

WORKER_HEARTBEAT_KEY = "arq:worker:heartbeat"


async def run_import_job(ctx: dict[str, Any], import_id: str) -> None:
    """ARQ job entry point for processing a question paper import."""
    logger.info("ARQ executing import job for import_id: %s", import_id)
    await process_question_import(import_id)


async def run_answer_key_job(ctx: dict[str, Any], import_id: str) -> None:
    """ARQ job entry point for processing an answer key import."""
    logger.info("ARQ executing answer key job for import_id: %s", import_id)
    await process_answer_key_import(import_id)


async def startup(ctx: dict[str, Any]) -> None:
    """Startup hook to establish worker presence in Redis."""
    logger.info("ExamArena ARQ worker starting up...")
    redis = ctx.get("redis")
    if redis:
        try:
            await redis.set(WORKER_HEARTBEAT_KEY, "healthy", ex=30)
            logger.info("Worker heartbeat registered in Redis.")
        except Exception as e:
            logger.warning("Could not set initial worker heartbeat: %s", e)


async def shutdown(ctx: dict[str, Any]) -> None:
    """Shutdown hook to clean up worker presence."""
    logger.info("ExamArena ARQ worker shutting down...")
    redis = ctx.get("redis")
    if redis:
        try:
            await redis.delete(WORKER_HEARTBEAT_KEY)
        except Exception:
            pass


def get_redis_settings(url: str | None = None) -> RedisSettings:
    """Safely constructs an ARQ RedisSettings instance, normalizing missing scheme prefixes."""
    raw_url = url or settings.REDIS_URL
    if not raw_url:
        return RedisSettings()
    clean_url = str(raw_url).strip()
    if not clean_url.startswith(("redis://", "rediss://", "unix://")):
        clean_url = f"redis://{clean_url}"
    try:
        return RedisSettings.from_dsn(clean_url)
    except Exception as e:
        logger.warning("Could not parse Redis DSN %s: %s", clean_url, e)
        return RedisSettings()


async def check_worker_availability() -> dict[str, Any]:
    """Inspects Redis connection and determines if an active ARQ worker is consuming jobs."""
    if not settings.REDIS_URL:
        return {
            "redis_configured": False,
            "redis_connected": False,
            "worker_available": False,
            "detail": "Redis is not configured in this environment.",
        }

    try:
        from arq import create_pool

        pool = await create_pool(get_redis_settings())
        try:
            health = await pool.get("arq:queue:health-check")
            heartbeat = await pool.get(WORKER_HEARTBEAT_KEY)
            is_alive = bool(health or heartbeat)
            return {
                "redis_configured": True,
                "redis_connected": True,
                "worker_available": is_alive,
                "health_check": health.decode() if isinstance(health, bytes) else health,
                "detail": (
                    "Worker is active and consuming jobs."
                    if is_alive
                    else "Redis reachable, but no active ARQ worker detected."
                ),
            }
        finally:
            await pool.aclose()
    except Exception as e:
        return {
            "redis_configured": True,
            "redis_connected": False,
            "worker_available": False,
            "detail": f"Failed to connect to Redis: {str(e)}",
        }


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [run_import_job, run_answer_key_job]
    redis_settings = get_redis_settings()
    max_jobs = 10
    job_timeout = 300
    health_check_interval = 15
    health_check_key = "arq:queue:health-check"
    on_startup = startup
    on_shutdown = shutdown
