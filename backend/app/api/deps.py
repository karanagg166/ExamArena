from fastapi import Cookie, HTTPException, status

from app.audit.context import set_current_actor
from app.core.rbac import (
    check_rbac_permission,
    enforce_rbac_permission,
    get_casbin_enforcer,
    require_rbac_permission,
)
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
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    from app.core.security import decode_token_claims

    claims = decode_token_claims(access_token)
    jti = claims.get("jti") if claims else None
    if jti:
        from app.auth.token_blacklist import (
            TokenBlacklistUnavailableError,
            is_token_blacklisted,
        )

        try:
            if await is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )
        except TokenBlacklistUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            ) from exc

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    set_current_actor(user.id, user.email, user.role)
    return user


async def get_current_staff_teacher(
    current_user: UserResponse | None = None,
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
