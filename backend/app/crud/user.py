from prisma import Prisma
from app.core.security import hash_password

prisma = Prisma()

async def get_user_by_email(email: str):
    """Get user by email"""
    return await prisma.user.find_unique(where={"email": email})

async def get_user_by_id(user_id: int):
    """Get user by ID"""
    return await prisma.user.find_unique(where={"id": user_id})

async def create_user(email: str, full_name: str, password: str, role: str = "student"):
    """Create new user"""
    hashed_password = hash_password(password)
    return await prisma.user.create(
        data={
            "email": email,
            "fullName": full_name,
            "password": hashed_password,
            "role": role
        }
    )
