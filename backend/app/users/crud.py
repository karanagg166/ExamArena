import app.core.database as db
from app.core.security import hash_password
from datetime import datetime
from app.users.schemas import UserRequest


async def get_user_by_email(email: str):
    """Get user by email"""
    return await db.prisma.user.find_unique(where={"email": email})


async def get_user_by_id(user_id: str):
    """Get user by ID"""
    return await db.prisma.user.find_unique(where={"id": user_id})  # type: ignore


async def create_user(user_data: UserRequest):
    """Create new user"""
    hashed_password = hash_password(user_data.password)

    # Dump Pydantic object, replace raw password with hashed
    data_dict = user_data.model_dump(exclude={"password"})
    data_dict["password"] = hashed_password
    
    user = await prisma.user.create(data=data_dict)

    role = user.role.upper()

    if role == "STUDENT":
        await prisma.student.create(
            data={
                "userId": user.id,
                "rollNo": "NA",  
                "dob": datetime.utcnow(),      
                "class_": "NA",                 
                "parentName": "NA",
                "parentEmail": "na@example.com",
            }
        )

    elif role == "TEACHER":
        await prisma.teacher.create(
            data={
                "userId": user.id,
                "qualification": "NA",
                "experience": 0,
                "department": "General",
            }
        )

    elif role == "PRINCIPAL":
        await prisma.principal.create(
            data={
                "userId": user.id,
                "qualification": "NA",
                "experience": 0,
            }
        )

    return user

async def update_user(user_id: str, user_data):
    """Update user data"""
    update_dict = user_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        # No data to update, return current user
        return await prisma.user.find_unique(where={"id": user_id})
    
    return await prisma.user.update(
        where={"id": user_id},
        data=update_dict
    )
