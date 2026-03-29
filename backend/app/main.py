import sentry_sdk
from fastapi import FastAPI, HTTPException
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


@app.on_event("startup")
async def startup():
    await db.prisma.connect()
    print("✅ Database connected")


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
    try:
        # Don't connect/disconnect — just check if it's already connected
        if not db.prisma.is_connected():
            raise Exception("Prisma not connected")
        return {"status": "healthy"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="unhealthy") from exc


@app.get("/sentry-debug")
async def trigger_error():
    # This intentionally causes a ZeroDivisionError which Sentry will intercept
    raise ZeroDivisionError("Sentry debug endpoint")
