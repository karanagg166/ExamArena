from fastapi import APIRouter, HTTPException, status, Depends
from app.students.schemas import StudentResponse, StudentUpdate
from app.students.crud import get_student_by_user_id, update_student
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/students", tags=["students"])

@router.get("/me", response_model=StudentResponse)
async def get_my_student_data(current_user = Depends(get_current_user)):
    """Get current user's student data"""
    student = await get_student_by_user_id(current_user.id)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student data not found"
        )
    
    return student

@router.put("/me", response_model=StudentResponse)
async def update_my_student_data(
    student_data: StudentUpdate,
    current_user = Depends(get_current_user)
):
    """Update current user's student data"""
    # Check if student record exists
    existing_student = await get_student_by_user_id(current_user.id)
    
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student data not found"
        )
    
    # Update student data
    updated_student = await update_student(current_user.id, student_data)
    return updated_student

@router.get("/{user_id}", response_model=StudentResponse)
async def get_student_by_id(user_id: str, current_user = Depends(get_current_user)):
    """Get student data by user ID (admin/teacher access)"""
    student = await get_student_by_user_id(user_id)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return student
