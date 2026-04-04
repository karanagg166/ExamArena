from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from prisma.enums import Role

from app.api.deps import get_current_user
from app.principals.crud import get_principal_by_teacher_id
from app.students.crud import (
    create_student,
    get_student_by_id,
    get_student_by_user_id,
    get_students,
    update_student,
)
from app.students.schemas import (
    StudentCreate,
    StudentCreateRequest,
    StudentFilterParams,
    StudentListItemResponse,
    StudentResponse,
    StudentUpdate,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/students", tags=["students"])


@router.get("/", response_model=list[StudentListItemResponse])
async def fetch_students(
    name: str | None = None,
    email: str | None = None,
    rollNo: str | None = None,
    classYear: str | None = None,
    section: str | None = None,
    schoolName: str | None = None,
    schoolCode: str | None = None,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
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
