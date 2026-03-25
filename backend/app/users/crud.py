from datetime import datetime, timezone
from app.users.schemas import UserRequest
import app.core.database as db
from app.core.security import hash_password

async def get_user_by_email(email: str):
    """Get user by email"""
    return await db.prisma.user.find_unique(where={"email": email})

async def get_user_by_id(user_id: str):
    """Get user by ID"""
    return await db.prisma.user.find_unique(where={"id": user_id})

async def create_user(user_data: UserRequest):
    """Create new user with their corresponding profile atomically"""
    hashed_password = hash_password(user_data.password)
    print("User Data:", user_data)  # type: ignore
    # 1. Prepare base user data
    data_dict = user_data.model_dump(exclude={"password", "role"})
    data_dict["password"] = hashed_password
    data_dict["role"] = user_data.role.upper() # Ensure uppercase for Enum
     # 3. Create the user AND their profile in one single database transaction
    user = await db.prisma.user.create(
        data=data_dict, # type: ignore
       
    )

    return user

async def update_user(user_id: str, user_data):
    """Update user data"""
    update_dict = user_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        return await db.prisma.user.find_unique(where={"id": user_id})
    
    return await db.prisma.user.update(
        where={"id": user_id},
        data=update_dict
    )