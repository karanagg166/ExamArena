from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.users.schemas import UserResponse


class StudentFilterParams(BaseModel):
    """Query params for filtering the student list"""

    name: str | None = None
    email: str | None = None
    rollNo: str | None = None
    classYear: str | None = None
    section: str | None = None
    schoolName: str | None = None
    schoolCode: str | None = None
    scopeClassId: str | None = None
    scopeSchoolId: str | None = None


class StudentListItemResponse(BaseModel):
    """Lightweight student data for list views"""

    id: str
    userId: str
    rollNo: str
    classId: str
    schoolId: str
    name: str
    email: str
    phoneNo: str | None = None

    class Config:
        from_attributes = True



class StudentCreateRequest(BaseModel):
    """What the frontend sends — no userId (injected from JWT)"""

    rollNo: str
    parentName: str
    parentEmail: EmailStr
    schoolId: str
    classId: str  # ID of the SchoolClass the student joins


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
    parentName: str | None = None
    parentEmail: EmailStr | None = None
    schoolId: str | None = None
    classId: str | None = None


class StudentResponse(BaseModel):
    id: str
    userId: str
    rollNo: str
    parentName: str
    parentEmail: str
    dateOfAdmission: datetime
    schoolId: str
    classId: str
    user: UserResponse

    class Config:
        from_attributes = True
        populate_by_name = True
