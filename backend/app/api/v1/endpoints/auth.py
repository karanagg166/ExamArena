from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response
from prisma import Prisma
from app.schemas.user import LoginRequest, SignupRequest, UserResponse
from app.core.security import verify_password, create_access_token
from app.core.config import ENVIRONMENT, ACCESS_TOKEN_EXPIRE_MINUTES
from app.crud.user import get_user_by_email, create_user as crud_create_user
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
prisma = Prisma()

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: SignupRequest, response: Response):
    """
    Register new user
    - Creates account
    - Returns JWT in secure HttpOnly cookie
    """
    
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = await crud_create_user(
        email=user_data.email,
        full_name=user_data.fullName,
        password=user_data.password
    )
    
    # Generate token
    access_token = create_access_token(new_user.id)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return new_user

@router.post("/login", response_model=UserResponse)
async def login(credentials: LoginRequest, response: Response):
    """
    Login with email and password
    - Returns JWT in secure HttpOnly cookie
    """
    
    # Find user
    user = await get_user_by_email(credentials.email)
    
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    access_token = create_access_token(user.id)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return user

@router.post("/logout")
async def logout(response: Response):
    """Logout - clears token cookie"""
    response.delete_cookie(key="access_token", httponly=True)
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user
