from app.core.database import prisma
from app.students.schemas import StudentCreate, StudentUpdate

async def get_student_by_user_id(user_id: str):
    """Get student by user ID with user data"""
    return await prisma.student.find_unique(
        where={"userId": user_id},
        include={"user": True}
    )

async def create_student(student_data: StudentCreate):
    """Create student record"""
    return await prisma.student.create(data={
        "userId": student_data.userId,
        "rollNo": student_data.rollNo,
        "dob": student_data.dob,
        "class": student_data.class_,
        "parentName": student_data.parentName,
        "parentEmail": student_data.parentEmail,
    })

async def update_student(user_id: str, student_data: StudentUpdate):
    """Update student record and associated user data"""
    update_dict = student_data.model_dump(exclude_unset=True)
    
    # Extract user data if present
    user_data = update_dict.pop("user", None)
    
    # Update user data if provided
    if user_data:
        await prisma.user.update(
            where={"id": user_id},
            data=user_data
        )
    
    # Map class_ to class for database
    if "class_" in update_dict:
        update_dict["class_"] = update_dict.pop("class_")
    
    # Update student data if any student-specific fields are provided
    if update_dict:
        await prisma.student.update(
            where={"userId": user_id},
            data=update_dict
        )
    
    # Return updated student with user data
    return await get_student_by_user_id(user_id)

async def delete_student(user_id: str):
    """Delete student record"""
    return await prisma.student.delete(where={"userId": user_id})
