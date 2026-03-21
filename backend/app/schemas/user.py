from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    """Request body for login"""
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    """Request body for signup"""
    email: EmailStr
    fullName: str
    password: str

class UserResponse(BaseModel):
    """User data in response"""
    id: int
    email: str
    fullName: str
    role: str
    
    class Config:
        from_attributes = True
