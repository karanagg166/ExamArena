from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from jose import jwt

from app.api.deps import get_current_user
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.users.crud import (
    change_user_password as crud_change_password,
)
from app.users.crud import (
    create_user as crud_create_user,
)
from app.users.crud import (
    get_user_by_email,
    update_user,
)
from app.users.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    UserRequest,
    UserResponse,
    UserUpdate,
)

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
        await record_audit_event(
            action=AuditAction.AUTH_SIGNUP,
            resource_type=AuditResourceType.USER,
            status="FAILURE",
            metadata={"reason": "EMAIL_ALREADY_REGISTERED", "email": user_data.email},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    new_user = await crud_create_user(user_data)

    # Record persistent audit event
    await record_audit_event(
        action=AuditAction.AUTH_SIGNUP,
        resource_type=AuditResourceType.USER,
        resource_id=new_user.id,
        actor_id=new_user.id,
        actor_email=new_user.email,
        actor_role=new_user.role,
        status="SUCCESS",
        metadata={"role": new_user.role, "name": new_user.name},
    )

    # Generate token
    access_token = create_access_token(new_user.id)
    # Set cookie
    is_production = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
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
        await record_audit_event(
            action=AuditAction.AUTH_LOGIN_FAILED,
            resource_type=AuditResourceType.AUTH,
            status="FAILURE",
            metadata={"reason": "INVALID_EMAIL", "email": credentials.email},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email"
        )
    if not verify_password(credentials.password, user.password):
        await record_audit_event(
            action=AuditAction.AUTH_LOGIN_FAILED,
            resource_type=AuditResourceType.AUTH,
            resource_id=user.id,
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role,
            status="FAILURE",
            metadata={"reason": "INVALID_PASSWORD"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password"
        )

    # Generate token
    access_token = create_access_token(user.id)

    # Record persistent audit event
    await record_audit_event(
        action=AuditAction.AUTH_LOGIN_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        resource_id=user.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_role=user.role,
        status="SUCCESS",
        metadata={"role": user.role},
    )

    is_production = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout - clears token cookie"""
    await record_audit_event(
        action=AuditAction.AUTH_LOGOUT,
        resource_type=AuditResourceType.AUTH,
        status="SUCCESS",
    )
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
    updated = await update_user(current_user.id, user_data)
    await record_audit_event(
        action=AuditAction.USER_PROFILE_UPDATED,
        resource_type=AuditResourceType.USER,
        resource_id=current_user.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        status="SUCCESS",
    )
    return updated


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Change current user password"""
    await crud_change_password(
        user_id=current_user.id,
        current_password=body.currentPassword,
        new_password=body.newPassword,
    )
    await record_audit_event(
        action=AuditAction.AUTH_PASSWORD_CHANGED,
        resource_type=AuditResourceType.USER,
        resource_id=current_user.id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        status="SUCCESS",
    )
    return {"message": "Password changed successfully"}


@router.get("/stream-token")
async def get_stream_token(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """
    Generate GetStream secure user token for Stream Chat
    """
    if not settings.STREAM_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stream API Secret not configured in backend Settings.",
        )

    payload = {"user_id": current_user.id}

    token = jwt.encode(payload, settings.STREAM_API_SECRET, algorithm="HS256")

    return {
        "token": token,
        "apiKey": settings.STREAM_API_KEY,
        "appId": settings.STREAM_APP_ID,
    }
