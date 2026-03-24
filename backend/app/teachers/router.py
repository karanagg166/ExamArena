from fastapi import APIRouter, HTTPException, status, Depends
from app.teachers.schemas import TeacherResponse, TeacherUpdate
from app.teachers.crud import get_teacher_by_user_id, update_teacher
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/teachers", tags=["teachers"])

@router.get("/me", response_model=TeacherResponse)
async def get_my_teacher_data(current_user = Depends(get_current_user)):
    """Get current user's teacher data"""
    teacher = await get_teacher_by_user_id(current_user.id)
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher data not found"
        )
    
    return teacher

@router.put("/me", response_model=TeacherResponse)
async def update_my_teacher_data(
    teacher_data: TeacherUpdate,
    current_user = Depends(get_current_user)
):
    """Update current user's teacher data"""
    # Check if teacher record exists
    existing_teacher = await get_teacher_by_user_id(current_user.id)
    
    if not existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher data not found"
        )
    
    # Update teacher data
    updated_teacher = await update_teacher(current_user.id, teacher_data)
    return updated_teacher

@router.get("/{user_id}", response_model=TeacherResponse)
async def get_teacher_by_id(user_id: str, current_user = Depends(get_current_user)):
    """Get teacher data by user ID (admin access)"""
    teacher = await get_teacher_by_user_id(user_id)
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher
