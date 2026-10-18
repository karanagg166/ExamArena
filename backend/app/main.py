import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core import database as db
from app.core.config import settings
from app.core.middleware import RequestCorrelationAndLoggingMiddleware
from app.core.redis import connect_redis, disconnect_redis
from app.sockets import socket_router

logger = logging.getLogger(__name__)


async def connect_with_retry(attempts: int = 5, base_delay: int = 2) -> None:
    """Attempt to connect to the database with simple backoff to handle transient failures."""

    for attempt in range(1, attempts + 1):
        try:
            await db.init_db()
            logger.info("✅ Database connected and initialized")
            return
        except Exception as exc:
            if attempt == attempts:
                raise

            wait = base_delay * attempt
            logger.warning(
                f"⚠️ Database connect attempt {attempt}/{attempts} failed: {exc}. "
                f"Retrying in {wait}s..."
            )
            await asyncio.sleep(wait)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown logic."""
    if not os.getenv("VERCEL"):
        try:
            await connect_with_retry()
        except Exception as exc:
            logger.warning("Database initialization failed during startup: %s", exc)
    else:
        logger.info("Running on Vercel serverless environment; skipping startup DDL migrations.")

    try:
        await asyncio.wait_for(connect_redis(), timeout=4.0)
    except Exception as exc:
        logger.warning("Redis initialization timed out or failed: %s", exc)

    yield

    if not os.getenv("VERCEL"):
        try:
            await db.close_db()
        except Exception:
            pass
        try:
            await disconnect_redis()
        except Exception:
            pass
        logger.info("🔌 Database and Redis disconnected")


app = FastAPI(
    title="ExamArena API",
    description="Backend API for ExamArena",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestCorrelationAndLoggingMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.exception(f"Unhandled server exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred on the server."},
    )


# Include routers
app.include_router(api_router)
app.include_router(socket_router)


@app.get("/")
def root():
    return {
        "message": "ExamArena Backend API",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health")
@app.get("/health/live")
@app.get("/api/health")
@app.get("/api/health/live")
async def health_live():
    """Liveness probe: returns 200 if the FastAPI application process is alive."""
    return {
        "status": "ok",
        "service": "exam-arena-api",
        "environment": settings.ENVIRONMENT,
    }


_db_schema_ready = False


async def ensure_db_schema_ready() -> None:
    global _db_schema_ready
    if not _db_schema_ready:
        try:
            await db.init_db()
            _db_schema_ready = True
        except Exception as exc:
            logger.warning("Schema readiness migration execution failed: %s", exc)


@app.get("/health/ready")
@app.get("/api/health/ready")
async def health_ready():
    """Readiness probe: validates connectivity to PostgreSQL and Redis.

    Fails with HTTP 503 if any required dependency is unreachable.
    """
    from sqlalchemy import text

    await ensure_db_schema_ready()

    db_status = "unknown"
    redis_status = "unknown"
    errors: list[str] = []

    # 1. Database check
    try:
        async with db.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                db_status = "connected"
            else:
                db_status = "unhealthy"
                errors.append("Database query returned unexpected scalar")
    except Exception as exc:
        db_status = "disconnected"
        errors.append(f"Database error: {exc}")

    # 2. Redis check
    if settings.REDIS_URL:
        try:
            from app.core.redis import get_redis

            r = get_redis()
            if r:
                pong = await r.ping()
                redis_status = "connected" if pong else "unresponsive"
            else:
                redis_status = "not_initialized"
                errors.append("Redis client not initialized")
        except Exception as exc:
            redis_status = "disconnected"
            errors.append(f"Redis error: {exc}")
    else:
        redis_status = "not_configured"

    is_ready = db_status == "connected" and (redis_status in ("connected", "not_configured"))
    resp_code = 200 if is_ready else 503
    return JSONResponse(
        status_code=resp_code,
        content={
            "status": "ready" if is_ready else "unready",
            "service": "exam-arena-api",
            "database": db_status,
            "redis": redis_status,
            "environment": settings.ENVIRONMENT,
            "errors": errors if errors else None,
        },
    )


@app.get("/health/worker")
@app.get("/api/health/worker")
async def health_worker():
    """Worker availability probe: validates ARQ worker heartbeat in Redis.

    Returns 200 if worker is active, 503 if inactive or Redis unreachable.
    """
    from app.imports.worker import check_worker_availability

    status_data = await check_worker_availability()
    resp_code = 200 if status_data.get("worker_available") else 503
    return JSONResponse(status_code=resp_code, content=status_data)
