from fastapi import APIRouter, HTTPException, status, Depends
from app.students.schemas import StudentResponse, StudentUpdate, StudentCreate, StudentCreateRequest
from app.students.crud import get_student_by_user_id, update_student, create_student
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/students", tags=["students"])


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_my_student_profile(
    student_data: StudentCreateRequest,
    current_user=Depends(get_current_user)
):
    """Create student profile for the currently logged-in user"""
    existing = await get_student_by_user_id(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student profile already exists"
        )
    create_payload = StudentCreate(**student_data.model_dump(), userId=current_user.id)
    return await create_student(create_payload)


@router.get("/me", response_model=StudentResponse)
async def get_my_student_data(current_user=Depends(get_current_user)):
    """Get current user's student data"""
    student = await get_student_by_user_id(current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Please complete your profile setup."
        )
    return student


@router.put("/me", response_model=StudentResponse)
async def update_my_student_data(
    student_data: StudentUpdate,
    current_user=Depends(get_current_user)
):
    """Update current user's student data"""
    existing = await get_student_by_user_id(current_user.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    return await update_student(current_user.id, student_data)


@router.get("/{user_id}", response_model=StudentResponse)
async def get_student_by_id(user_id: str, current_user=Depends(get_current_user)):
    """Get student data by user ID (admin/teacher access)"""
    student = await get_student_by_user_id(user_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student
