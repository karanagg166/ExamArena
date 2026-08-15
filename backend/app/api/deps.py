from fastapi import Cookie, HTTPException, status

from app.core.security import verify_token
from app.users.crud import get_user_by_id
from app.users.schemas import UserResponse


async def get_current_user(access_token: str = Cookie(None)):
    """Dependency to get current authenticated user"""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    user_id = verify_token(access_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


async def get_current_staff_teacher(
    current_user: UserResponse = None,
):
    """Dependency to get the Teacher profile for TEACHER, PRINCIPAL, or ADMIN roles."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    if current_user.role not in ("TEACHER", "PRINCIPAL", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers or principals can perform this action",
        )

    from app.teachers.crud import get_teacher_by_user_id

    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff teacher profile not found. Please complete profile setup.",
        )
    return teacher
