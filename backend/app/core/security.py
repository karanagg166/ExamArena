from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings

def hash_password(password: str) -> str:
    """Convert plain password to hashed password"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches hashed password"""
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

def create_access_token(user_id: str) -> str:
    """Generate JWT token for user"""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def verify_token(token: str) -> str:
    """Extract user_id from token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub") # type: ignore
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None # type: ignore
