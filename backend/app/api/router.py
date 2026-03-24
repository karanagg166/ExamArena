from fastapi import APIRouter
from app.auth.router import router as auth_router
from app.students.router import router as students_router
from app.teachers.router import router as teachers_router
from app.principals.router import router as principals_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(principals_router)
