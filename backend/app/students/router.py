from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.attempts.crud import get_student_exam_history
from app.attempts.schemas import StudentExamHistoryItem
from app.core.database import get_db
from app.core.models import Role
from app.core.school_access import require_staff_class, resolve_staff_access
from app.students.crud import (
    get_student_by_id,
    get_student_by_user_id,
    get_students,
    update_student,
)
from app.students.schemas import (
    StudentFilterParams,
    StudentListItemResponse,
    StudentResponse,
    StudentUpdate,
)
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/students", tags=["students"])


@router.get("", response_model=list[StudentListItemResponse])
async def fetch_students(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    name: str | None = None,
    email: str | None = None,
    rollNo: str | None = None,
    classYear: str | None = None,
    section: str | None = None,
    schoolName: str | None = None,
    schoolCode: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List private student records within self or current staff class grants."""
    filters = StudentFilterParams(
        name=name,
        email=email,
        rollNo=rollNo,
        classYear=classYear,
        section=section,
        schoolName=schoolName,
        schoolCode=schoolCode,
    )
    if current_user.role == Role.STUDENT:
        me = await get_student_by_user_id(current_user.id, session=db)
        if not me:
            raise HTTPException(403, "Student profile not found.")
        filters.scopeUserId = current_user.id
        filters.scopeClassId = me.classId
        filters.scopeSchoolId = me.schoolId
    else:
        access = await resolve_staff_access(current_user, db)
        filters.scopeSchoolId = access.school_id
        filters.scopeClassIds = access.class_ids

    return await get_students(filters, session=db)


@router.get("/me", response_model=StudentResponse)
async def get_my_student_data(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get current user's student data"""
    student = await get_student_by_user_id(current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Please complete your profile setup.",
        )
    return student


@router.put("/me", response_model=StudentResponse)
async def update_my_student_data(
    student_data: StudentUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update current user's student data (rollNo, classId & schoolId cannot be updated by student)"""
    existing = await get_student_by_user_id(current_user.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found"
        )
    student_data.rollNo = None
    student_data.classId = None
    student_data.schoolId = None
    return await update_student(current_user.id, student_data)


async def _require_student_access(current_user, student, db):
    if current_user.role == Role.STUDENT:
        if student.userId != current_user.id:
            raise HTTPException(403, "Students can only access their own records.")
        return
    await require_staff_class(current_user, student.schoolId, student.classId, db)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student_by_id_endpoint(
    student_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get student data by primary ID with role-based access control"""
    student = await get_student_by_id(student_id, session=db)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    await _require_student_access(current_user, student, db)

    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student_by_id_endpoint(
    student_id: str,
    student_data: StudentUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update student data by ID (Teacher / Principal / Admin only)"""
    if current_user.role == Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot edit other students' profiles or roll numbers.",
        )

    student = await get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    await _require_student_access(current_user, student, db)

    return await update_student(student.userId, student_data)


@router.get("/{student_id}/exams", response_model=list[StudentExamHistoryItem])
async def get_student_exam_history_endpoint(
    student_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get complete exam history and scores for a student (Assigned teachers, school principals, or self)"""
    student = await get_student_by_id(student_id, session=db)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    await _require_student_access(current_user, student, db)

    history = await get_student_exam_history(student_id, session=db)
    if current_user.role == Role.STUDENT:
        redacted = []
        for item in history:
            item_copy = dict(item) if isinstance(item, dict) else item.model_dump()
            if not item_copy.get("isResultsReleased"):
                item_copy["marksObtained"] = None
                item_copy["percentage"] = None
            redacted.append(item_copy)
        return redacted

    return history
