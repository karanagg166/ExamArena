import uuid
from datetime import UTC, datetime, timedelta

import bcrypt

# pyrefly: ignore [missing-source-for-stubs]
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Convert plain password to hashed password"""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches hashed password"""
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    """Generate JWT token for user"""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "jti": str(uuid.uuid4())}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def decode_token_claims(token: str) -> dict | None:
    """Decode JWT token and return full claims dictionary, or None if invalid/expired."""
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return None


def verify_token(token: str) -> str | None:
    """Extract user_id string from token. Returns user_id or None."""
    payload = decode_token_claims(token)
    if not payload:
        return None
    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None
    return user_id
