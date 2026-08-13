import asyncio
import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.router import api_router
from app.core import database as db
from app.core.config import settings
from app.core.redis import connect_redis, disconnect_redis

logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=True,
    )


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
    await connect_with_retry()
    await connect_redis()
    yield
    await db.close_db()
    await disconnect_redis()
    logger.info("🔌 Database and Redis disconnected")


app = FastAPI(
    title="ExamArena API",
    description="Backend API for ExamArena",
    version="1.0.0",
    lifespan=lifespan,
)

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


@app.get("/")
def root():
    return {
        "message": "ExamArena Backend API",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/sentry-debug")
async def trigger_error():
    # This intentionally causes a ZeroDivisionError which Sentry will intercept
    raise ZeroDivisionError("Sentry debug endpoint")
