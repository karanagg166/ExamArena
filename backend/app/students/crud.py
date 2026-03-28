import app.core.database as db
from app.students.schemas import StudentCreate, StudentUpdate


async def get_student_by_user_id(user_id: str):
    """Get student by user ID with user data"""
    return await db.prisma.student.find_unique(
        where={"userId": user_id},
        include={"user": True}
    )


async def get_student_by_id(student_id: str):
    """Get student by primary ID with user data"""
    return await db.prisma.student.find_unique(
        where={"id": student_id},
        include={"user": True}
    )


async def create_student(student_data: StudentCreate):
    """Create student record"""
    await db.prisma.student.create(data={
        "userId": student_data.userId,
        "rollNo": student_data.rollNo,
        "dob": student_data.dob,
        "parentName": student_data.parentName,
        "parentEmail": student_data.parentEmail,
        "dateOfAdmission": student_data.dateOfAdmission,
        "schoolId": student_data.schoolId,
        "classId": student_data.classId,
    })
    return await get_student_by_user_id(student_data.userId)


async def update_student(user_id: str, student_data: StudentUpdate):
    """Update student record and associated user data"""
    update_dict = student_data.model_dump(exclude_unset=True)

    # Extract user data if present
    user_data = update_dict.pop("user", None)

    # Update user data if provided
    if user_data:
        await db.prisma.user.update(
            where={"id": user_id},
            data=user_data
        )

    # Update student data if any student-specific fields are provided
    if update_dict:
        await db.prisma.student.update(
            where={"userId": user_id},
            data=update_dict
        )

    return await get_student_by_user_id(user_id)


async def delete_student(user_id: str):
    """Delete student record"""
    return await db.prisma.student.delete(where={"userId": user_id})
