from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    """Request body for login"""
    email: EmailStr
    password: str

class UserRequest(BaseModel):
    """Request body for signup and user creation"""
    email: EmailStr
    name: str
    password: str
    phoneNo: str
    pincode: str
    city: str
    state: str
    country: str
    role: str

class UserResponse(BaseModel):
    """User data in response"""
    id: str
    email: str
    name: str
    phoneNo: str
    pincode: str
    city: str
    state: str
    country: str
    role: str
    
    class Config:
        from_attributes = True
