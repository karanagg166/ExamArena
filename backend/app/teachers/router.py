from fastapi import APIRouter, HTTPException, status, Depends
from app.teachers.schemas import TeacherResponse, TeacherUpdate, TeacherCreate, TeacherCreateRequest
from app.teachers.crud import get_teacher_by_user_id, update_teacher, create_teacher, get_all_qualifications,get_all_subjects
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/teachers", tags=["teachers"])


@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_my_teacher_profile(
    teacher_data: TeacherCreateRequest,
    current_user=Depends(get_current_user)):
    """Create teacher profile for the currently logged-in user"""
    print("Received teacher profile creation request:", teacher_data)
    print("Current user:", current_user)
    existing = await get_teacher_by_user_id(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher profile already exists"
        )
    create_payload = TeacherCreate(**teacher_data.model_dump(), userId=current_user.id)
    print("Creating teacher profile with payload:", create_payload)
    return await create_teacher(create_payload)


@router.get("/me", response_model=TeacherResponse)
async def get_my_teacher_data(current_user=Depends(get_current_user)):
    """Get current user's teacher data"""
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found. Please complete your profile setup."
        )
    return teacher


@router.put("/me", response_model=TeacherResponse)
async def update_my_teacher_data(
    teacher_data: TeacherUpdate,
    current_user=Depends(get_current_user)
):
    """Update current user's teacher data"""
    existing = await get_teacher_by_user_id(current_user.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    return await update_teacher(current_user.id, teacher_data)


@router.get("/qualifications", response_model=list[str])
async def get_teacher_qualifications():
    """Get all possible qualifications for teachers"""
    return await get_all_qualifications()
@router.get("/subjects", response_model=list[str])
async def get_teacher_subjects():
    """Get all possible subjects for teachers"""
    return await get_all_subjects()

@router.get("/{user_id}", response_model=TeacherResponse)
async def get_teacher_by_id(user_id: str, current_user=Depends(get_current_user)):
    """Get teacher data by user ID (admin access)"""
    teacher = await get_teacher_by_user_id(user_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    return teacher
    