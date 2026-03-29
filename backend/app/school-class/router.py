from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from prisma.enums import Role

from app.api.deps import get_current_user
from app.principals.crud import get_principal_by_teacher_id
from app.students.crud import get_student_by_user_id, get_students_by_class_id
from app.students.schemas import StudentResponse
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

from .crud import (
    create_school_class,
    get_school_class_by_id,
    get_school_classes_by_school_id,
)
from .schemas import SchoolClassCreateRequest, SchoolClassResponse

router = APIRouter(prefix="/api/v1/classes", tags=["classes"])


@router.post(
    "/", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED
)
async def create_class(
    class_data: SchoolClassCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create a new school class."""
    print("Received class creation request:", class_data, "from user:", current_user.id)
    created_class = await create_school_class(class_data, current_user.id)
    if not created_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create classes for your own school.",
        )

    return created_class


@router.get("/school/{school_id}", response_model=list[SchoolClassResponse])
async def get_classes_for_school(
    school_id: str,
):
    """Get all classes for a specific school."""
    return await get_school_classes_by_school_id(school_id)


@router.get("/{class_id}", response_model=SchoolClassResponse)
async def get_class_by_id(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get a specific class by ID with RBAC stringency."""
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Authorization checks
    if current_user.role == Role.STUDENT:
        student = await get_student_by_user_id(current_user.id)
        if not student or student.classId != school_class.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own class.",
            )
    elif current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be a teacher at this school.",
            )
    elif current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
            )
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal or principal.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be the principal of this school.",
            )

    return school_class


@router.get("/{class_id}/students", response_model=list[StudentResponse])
async def get_students_for_class(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get all students for a specific class with RBAC."""
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Authorization checks
    if current_user.role == Role.STUDENT:
        student = await get_student_by_user_id(current_user.id)
        if not student or student.classId != school_class.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own class.",
            )
    elif current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be a teacher at this school.",
            )
    elif current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
            )
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal or principal.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be the principal of this school.",
            )

    return await get_students_by_class_id(class_id)
