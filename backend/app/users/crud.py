from app.core.database import prisma
from app.core.security import hash_password

async def get_user_by_email(email: str):
    """Get user by email"""
    return await prisma.user.find_unique(where={"email": email})

async def get_user_by_id(user_id: int):
    """Get user by ID"""
    return await prisma.user.find_unique(where={"id": user_id})

from app.users.schemas import UserRequest

async def create_user(user_data: UserRequest):
    """Create new user"""
    hashed_password = hash_password(user_data.password)
    
    # Dump Pydantic object, replace raw password with hashed
    data_dict = user_data.model_dump(exclude={"password"})
    data_dict["password"] = hashed_password
    
    return await prisma.user.create(data=data_dict)
