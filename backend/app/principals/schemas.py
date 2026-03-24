from pydantic import BaseModel
from app.users.schemas import UserResponse

class PrincipalBase(BaseModel):
    qualification: str
    experience: int

class PrincipalCreate(PrincipalBase):
    userId: str

class UserUpdateNested(BaseModel):
    name: str | None = None
    email: str | None = None
    phoneNo: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None

class PrincipalUpdate(BaseModel):
    user: UserUpdateNested | None = None
    qualification: str | None = None
    experience: int | None = None

class PrincipalResponse(PrincipalBase):
    id: str
    userId: str
    user: UserResponse
    
    class Config:
        from_attributes = True
