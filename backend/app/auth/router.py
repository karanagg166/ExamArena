from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.users.crud import (
    create_user as crud_create_user,
    get_user_by_email,
    update_user,
)
from app.users.schemas import LoginRequest, UserRequest, UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserRequest, response: Response):
    """
    Register new user
    - Creates account
    - Returns JWT in secure HttpOnly cookie
    """

    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    new_user = await crud_create_user(user_data)

    # Generate token
    access_token = create_access_token(new_user.id)
    print("created user token is here", access_token)  # type: ignore
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
        )
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password"
        )

    # Generate token
    access_token = create_access_token(user.id)

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout - clears token cookie"""
    response.delete_cookie(key="access_token", httponly=True)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get current authenticated user"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update current authenticated user"""
    return await update_user(current_user.id, user_data)
