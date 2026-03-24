from pydantic import BaseModel
from app.users.schemas import UserResponse

class TeacherBase(BaseModel):
    qualification: str
    experience: int
    department: str

class TeacherCreate(TeacherBase):
    userId: str

class UserUpdateNested(BaseModel):
    name: str | None = None
    email: str | None = None
    phoneNo: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None

class TeacherUpdate(BaseModel):
    user: UserUpdateNested | None = None
    qualification: str | None = None
    experience: int | None = None
    department: str | None = None

class TeacherResponse(TeacherBase):
    id: str
    userId: str
    user: UserResponse
    
    class Config:
        from_attributes = True
