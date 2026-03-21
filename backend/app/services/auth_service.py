from fastapi import HTTPException, status
from app.core.database import db
from app.core.security import get_password_hash
from app.schemas.user import UserCreate

async def create_user(user_in: UserCreate):
    """
    Business logic for creating a new user.
    """
    # 1. Check if user already exists
    existing_user = await db.user.find_unique(where={"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # 2. Hash the password
    hashed_password = get_password_hash(user_in.password)
    
    # 3. Prepare data for Prisma
    # We dump the Pydantic model into a dict, exclude the raw password,
    # and insert the hashed password.
    user_data = user_in.model_dump(exclude={"password"})
    user_data["password"] = hashed_password
    
    # 4. Save to the database
    # NOTE: Your Pydantic schema contains fields like 'pincode', 'city', 'country', 'state' 
    # make sure they are also added to your `schema.prisma` inside the `User` model!
    new_user = await db.user.create(data=user_data)
    
    return new_user
