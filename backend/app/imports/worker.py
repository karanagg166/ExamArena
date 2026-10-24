"""Worker settings and ARQ job definitions for question paper and answer key imports."""

import logging
import urllib.parse
from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron

from app.answer_keys.service import process_answer_key_import
from app.core.config import settings
from app.imports.service import process_question_import

logger = logging.getLogger(__name__)

WORKER_HEARTBEAT_KEY = "arq:worker:heartbeat"


async def refresh_heartbeat(ctx: dict[str, Any]) -> None:
    """Cron task to refresh worker heartbeat in Redis periodically."""
    redis = ctx.get("redis")
    if redis:
        try:
            await redis.set(WORKER_HEARTBEAT_KEY, "healthy", ex=30)
        except Exception as e:
            logger.warning("Could not refresh worker heartbeat: %s", e)


async def run_import_job(ctx: dict[str, Any], import_id: str, generation: int = 1) -> None:
    """ARQ job entry point for processing a question paper import."""
    logger.info("ARQ executing import job for import_id: %s (generation: %d)", import_id, generation)
    await process_question_import(import_id, generation=generation)


async def run_answer_key_job(ctx: dict[str, Any], import_id: str, generation: int = 1) -> None:
    """ARQ job entry point for processing an answer key import."""
    logger.info("ARQ executing answer key job for import_id: %s (generation: %d)", import_id, generation)
    await process_answer_key_import(import_id, generation=generation)


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


def sanitize_redis_url(url: str | None) -> str:
    """Mask credentials in a Redis URL for safe logging and error reporting."""
    if not url:
        return ""
    raw = str(url).strip()
    try:
        parsed = urllib.parse.urlsplit(raw)
        netloc = parsed.netloc
        if "@" in netloc:
            auth, host_port = netloc.split("@", 1)
            if auth.startswith(":"):
                sanitized_auth = ":***"
            elif ":" in auth:
                sanitized_auth = "***:***"
            else:
                sanitized_auth = "***"
            netloc = f"{sanitized_auth}@{host_port}"
        return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
    except Exception:
        return "[SANITIZED_REDIS_URL]"


def get_redis_settings(url: str | None = None) -> RedisSettings:
    """Safely constructs an ARQ RedisSettings instance, normalizing missing scheme prefixes.

    Guarantees:
    - Never logs raw Redis DSNs, passwords, usernames, or credentials.
    - Accurately parses rediss:// and redis:// URLs with SSL/TLS parameters.
    - Fails securely on malformed DSNs instead of silently falling back to localhost.
    - Rejects localhost fallbacks in production environments.
    """
    raw_url = url if url is not None else settings.REDIS_URL
    is_prod = str(settings.ENVIRONMENT).lower() == "production"

    if not raw_url or not str(raw_url).strip():
        if is_prod:
            raise ValueError(
                "Production configuration failure: REDIS_URL must be configured with a valid non-empty DSN."
            )
        return RedisSettings()

    clean_url = str(raw_url).strip()
    if not clean_url.startswith(("redis://", "rediss://", "unix://")):
        clean_url = f"redis://{clean_url}"

    sanitized = sanitize_redis_url(clean_url)

    if is_prod:
        try:
            parsed = urllib.parse.urlsplit(clean_url)
            host = (parsed.hostname or "").lower()
            if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
                raise ValueError(
                    f"Production configuration failure: Localhost Redis ({sanitized}) is not permitted in production."
                )
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Production configuration failure: Malformed Redis DSN ({sanitized}): {exc}") from exc

    try:
        return RedisSettings.from_dsn(clean_url)
    except Exception as exc:
        logger.error("Could not parse Redis DSN %s: %s", sanitized, exc)
        raise ValueError(
            f"Failed to parse Redis DSN ({sanitized}): {exc}"
        ) from exc


async def check_worker_availability() -> dict[str, Any]:
    """Inspects Redis connection and determines if an active ARQ worker is consuming jobs."""
    if not settings.REDIS_URL:
        return {
            "service": settings.WORKER_SERVICE_NAME,
            "queue": "arq:queue",
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
                "service": settings.WORKER_SERVICE_NAME,
                "queue": "arq:queue",
                "redis_configured": True,
                "redis_connected": True,
                "worker_available": is_alive,
                "health_check": health.decode() if isinstance(health, bytes) else health,
                "heartbeat": heartbeat.decode() if isinstance(heartbeat, bytes) else heartbeat,
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
            "service": settings.WORKER_SERVICE_NAME,
            "queue": "arq:queue",
            "redis_configured": True,
            "redis_connected": False,
            "worker_available": False,
            "detail": f"Failed to connect to Redis: {str(e)}",
        }


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [run_import_job, run_answer_key_job]
    cron_jobs = [cron(refresh_heartbeat, second={0, 15, 30, 45})]
    redis_settings = get_redis_settings()
    max_jobs = 10
    job_timeout = 300
    health_check_interval = 15
    health_check_key = "arq:queue:health-check"
    on_startup = startup
    on_shutdown = shutdown
