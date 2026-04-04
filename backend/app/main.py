import asyncio

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.router import api_router
from app.core.config import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=True,
    )

import app.core.database as db

app = FastAPI(
    title="ExamArena API",
    description="Backend API for ExamArena",
    version="1.0.0",
)


async def connect_with_retry(attempts: int = 5, base_delay: int = 2) -> None:
    """Attempt to connect to the database with simple backoff to handle transient failures."""

    for attempt in range(1, attempts + 1):
        try:
            await db.prisma.connect()
            print("✅ Database connected")
            return
        except Exception as exc:
            if attempt == attempts:
                raise

            wait = base_delay * attempt
            print(
                f"⚠️ Database connect attempt {attempt}/{attempts} failed: {exc}. "
                f"Retrying in {wait}s..."
            )
            await asyncio.sleep(wait)


@app.on_event("startup")
async def startup():
    await connect_with_retry()


@app.on_event("shutdown")
async def shutdown():
    await db.prisma.disconnect()
    print("🔌 Database disconnected")


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
