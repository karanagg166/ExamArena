from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prisma import Prisma
from app.core.config import ALLOWED_ORIGINS, ENVIRONMENT
from app.api.v1.endpoints import auth

prisma = Prisma()  

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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)

@app.get("/")
def root():
    return {
        "message": "ExamArena Backend API",
        "environment": ENVIRONMENT,
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}