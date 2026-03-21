from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prisma import Prisma
from app.core.config import settings
from app.api.router import api_router
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=True,
    )

from app.core.database import prisma  

app = FastAPI(
    title="ExamArena API",
    description="Backend API for ExamArena",
    version="1.0.0",
)

@app.on_event("startup")
async def startup():
    await prisma.connect()
    print("✅ Database connected")

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()
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
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/sentry-debug")
async def trigger_error():
    # This intentionally causes a ZeroDivisionError which Sentry will intercept
    division_by_zero = 1 / 0