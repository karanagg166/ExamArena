from fastapi import APIRouter, status
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import create_user

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate):
    """
    Register a new user in the system.
    """
    # Call the service layer to handle the business logic
    new_user = await create_user(user_in)
    
    return new_user
