from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.attempts.crud import get_student_exam_history
from app.attempts.schemas import StudentExamHistoryItem
from app.core.models import Role
from app.principals.crud import get_principal_by_teacher_id
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
from app.teachers.crud import get_teacher_by_user_id
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
):
    """
    List students with optional filters.

    Access rules:
        - STUDENT: can only see students in their own class
    - TEACHER / PRINCIPAL: can see students in their school (schoolId scoped automatically)
    """
    # Determine scoping based on role
    if current_user.role == Role.STUDENT:
        me = await get_student_by_user_id(current_user.id)
        if not me:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student profile not found. Complete your profile first.",
            )
        # Students can only see classmates — force classId to their own class
        filters = StudentFilterParams(
            name=name,
            email=email,
            rollNo=rollNo,
            classYear=classYear,
            section=section,
            schoolName=schoolName,
            schoolCode=schoolCode,
            scopeClassId=me.classId,
            scopeSchoolId=me.schoolId,
        )
    elif current_user.role in (Role.TEACHER, Role.PRINCIPAL):
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or not teacher.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be assigned to a school to view its students.",
            )
        filters = StudentFilterParams(
            name=name,
            email=email,
            rollNo=rollNo,
            classYear=classYear,
            section=section,
            schoolName=schoolName,
            schoolCode=schoolCode,
            scopeSchoolId=teacher.schoolId,
        )
    else:
        # ADMIN or other — no restriction (can optionally filter)
        filters = StudentFilterParams(
            name=name,
            email=email,
            rollNo=rollNo,
            classYear=classYear,
            section=section,
            schoolName=schoolName,
            schoolCode=schoolCode,
        )

    return await get_students(filters)


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


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student_by_id_endpoint(
    student_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get student data by primary ID with role-based access control"""
    student = await get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # Authorization checks
    if current_user.role == Role.STUDENT:
        # Students can see their own profile OR same-class peers
        me = await get_student_by_user_id(current_user.id)
        if not me:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student profile not found.",
            )
        # Allow: same student or same class
        if student.userId != current_user.id and student.classId != me.classId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view profiles of students in your class.",
            )
    elif current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be a teacher at this student's school.",
            )
    elif current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
            )
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal or principal.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be the principal of this student's school.",
            )

    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student_by_id_endpoint(
    student_id: str,
    student_data: StudentUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
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

    if current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be a teacher at this student's school.",
            )
    elif current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
            )
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal or principal.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be the principal of this student's school.",
            )

    return await update_student(student.userId, student_data)


@router.get("/{student_id}/exams", response_model=list[StudentExamHistoryItem])
async def get_student_exam_history_endpoint(
    student_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get complete exam history and scores for a student (Staff from same school or self)"""
    student = await get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    if current_user.role == Role.STUDENT:
        me = await get_student_by_user_id(current_user.id)
        if not me or me.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own exam history.",
            )
    elif current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be a teacher at this student's school.",
            )
    elif current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be the principal of this student's school.",
            )

    return await get_student_exam_history(student_id)
