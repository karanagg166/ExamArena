import app.core.database as db
from app.core.security import hash_password
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
    user = await db.prisma.user.create(data=data_dict)  # type: ignore
    # token = create_access_token(user.id) # type: ignore
    # print("created user token is here",token) # type: ignore
    return user
