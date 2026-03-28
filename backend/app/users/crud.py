import app.core.database as db
from app.core.security import hash_password
from app.users.schemas import UserRequest, UserUpdate


async def get_user_by_email(email: str):
    """Retrieve a user by their email address."""
    return await db.prisma.user.find_unique(where={"email": email})


async def get_user_by_id(user_id: str):
    """Retrieve a user by their unique database ID."""
    return await db.prisma.user.find_unique(where={"id": user_id})


async def create_user(user_data: UserRequest):
    """
    Creates ONLY the base User account.
    Role-specific profiles (Student, Teacher) must be created in a later step.
    """
    # 1. Hash the password
    hashed_password = hash_password(user_data.password)

    # 2. Extract data and inject the hashed password and raw role string
    data_dict = user_data.model_dump(exclude={"password", "role"})
    data_dict["password"] = hashed_password
    data_dict["role"] = user_data.role.value

    # 3. Create ONLY the base user record
    user = await db.prisma.user.create(data=data_dict)  # type: ignore

    return user


async def update_user(user_id: str, user_data: UserUpdate):
    """Safely updates only the fields the user provided."""
    update_dict = user_data.model_dump(exclude_unset=True)

    if not update_dict:
        return await db.prisma.user.find_unique(where={"id": user_id})

    return await db.prisma.user.update(
        where={"id": user_id}, data=update_dict  # type: ignore
    )
