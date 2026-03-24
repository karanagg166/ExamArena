from app.core.database import prisma
from app.teachers.schemas import TeacherCreate, TeacherUpdate

async def get_teacher_by_user_id(user_id: str):
    """Get teacher by user ID with user data"""
    return await prisma.teacher.find_unique(
        where={"userId": user_id},
        include={"user": True}
    )

async def create_teacher(teacher_data: TeacherCreate):
    """Create teacher record"""
    return await prisma.teacher.create(data=teacher_data.model_dump())

async def update_teacher(user_id: str, teacher_data: TeacherUpdate):
    """Update teacher record and associated user data"""
    update_dict = teacher_data.model_dump(exclude_unset=True)
    
    # Extract user data if present
    user_data = update_dict.pop("user", None)
    
    # Update user data if provided
    if user_data:
        await prisma.user.update(
            where={"id": user_id},
            data=user_data
        )
    
    # Update teacher data if any teacher-specific fields are provided
    if update_dict:
        await prisma.teacher.update(
            where={"userId": user_id},
            data=update_dict
        )
    
    # Return updated teacher with user data
    return await get_teacher_by_user_id(user_id)

async def delete_teacher(user_id: str):
    """Delete teacher record"""
    return await prisma.teacher.delete(where={"userId": user_id})
