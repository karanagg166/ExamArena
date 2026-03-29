from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from prisma.enums import Role

from app.api.deps import get_current_user
from app.principals.crud import get_principal_by_teacher_id
from app.students.crud import (
    create_student,
    get_student_by_id,
    get_student_by_user_id,
    update_student,
)
from app.students.schemas import (
    StudentCreate,
    StudentCreateRequest,
    StudentResponse,
    StudentUpdate,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/students", tags=["students"])


@router.post(
    "/", response_model=StudentCreateRequest, status_code=status.HTTP_201_CREATED
)
async def create_my_student_profile(
    student_data: StudentCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create student profile for the currently logged-in user"""
    print(
        "Received student profile creation request:",
        student_data,
        "from user:",
        current_user.id,
    )
    existing = await get_student_by_user_id(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student profile already exists",
        )
    create_payload = StudentCreate(**student_data.model_dump(), userId=current_user.id)
    print("Creating student profile with data:", create_payload)
    return await create_student(create_payload)


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
    """Update current user's student data"""
    existing = await get_student_by_user_id(current_user.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found"
        )
    return await update_student(current_user.id, student_data)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student_by_id_endpoint(
    student_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get student data by primary ID (admin/teacher access)"""
    student = await get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # Authorization checks
    if current_user.role == Role.STUDENT:
        if student.userId != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own profile.",
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
