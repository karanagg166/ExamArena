from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.principals.router import router as principals_router
from app.school.router import router as school_router
from app.school_class.router import router as school_class_router
from app.students.router import router as students_router
from app.teachers.router import router as teachers_router
from app.exams.router import router as exams_router
from app.questions.router import router as questions_router
from app.attempts.router import router as attempts_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(principals_router)
api_router.include_router(school_router)
api_router.include_router(school_class_router)
api_router.include_router(exams_router)
api_router.include_router(questions_router)
api_router.include_router(attempts_router)
