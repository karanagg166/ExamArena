from datetime import datetime
from app.users.schemas import UserResponse
from pydantic import BaseModel, EmailStr


class StudentCreateRequest(BaseModel):
    """What the frontend sends — no userId (injected from JWT)"""
    rollNo: str
    dob: datetime
    parentName: str
    parentEmail: EmailStr
    dateOfAdmission: datetime
    classId: str   # ID of the SchoolClass the student joins


class StudentCreate(StudentCreateRequest):
    """Internal use — includes userId injected server-side"""
    userId: str


class UserUpdateNested(BaseModel):
    name: str | None = None
    email: str | None = None
    phoneNo: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None


class StudentUpdate(BaseModel):
    user: UserUpdateNested | None = None
    rollNo: str | None = None
    dob: datetime | None = None
    parentName: str | None = None
    parentEmail: EmailStr | None = None


class StudentResponse(BaseModel):
    id: str
    userId: str
    rollNo: str
    dob: datetime
    parentName: str
    parentEmail: str
    dateOfAdmission: datetime
    classId: str
    user: UserResponse

    class Config:
        from_attributes = True
        populate_by_name = True
