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
    className: str | None = None
    schoolId: str
    schoolName: str | None = None
    name: str
    email: str
    phoneNo: str | None = None

    class Config:
        from_attributes = True


class StudentCreateRequest(BaseModel):
    """What the frontend sends — no userId (injected from JWT)"""

    rollNo: str
    parentName: str | None = None
    parentEmail: EmailStr | str | None = None
    fatherName: str | None = None
    fatherEmail: EmailStr | str | None = None
    fatherPhoneNo: str | None = None
    motherName: str | None = None
    motherEmail: EmailStr | str | None = None
    motherPhoneNo: str | None = None
    guardianName: str | None = None
    guardianRelation: str | None = None
    guardianEmail: EmailStr | str | None = None
    guardianPhoneNo: str | None = None
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
    parentEmail: EmailStr | str | None = None
    fatherName: str | None = None
    fatherEmail: EmailStr | str | None = None
    fatherPhoneNo: str | None = None
    motherName: str | None = None
    motherEmail: EmailStr | str | None = None
    motherPhoneNo: str | None = None
    guardianName: str | None = None
    guardianRelation: str | None = None
    guardianEmail: EmailStr | str | None = None
    guardianPhoneNo: str | None = None
    schoolId: str | None = None
    classId: str | None = None


class StudentResponse(BaseModel):
    id: str
    userId: str
    rollNo: str
    parentName: str | None = None
    parentEmail: str | None = None
    fatherName: str | None = None
    fatherEmail: str | None = None
    fatherPhoneNo: str | None = None
    motherName: str | None = None
    motherEmail: str | None = None
    motherPhoneNo: str | None = None
    guardianName: str | None = None
    guardianRelation: str | None = None
    guardianEmail: str | None = None
    guardianPhoneNo: str | None = None
    dateOfAdmission: datetime
    schoolId: str
    schoolName: str | None = None
    classId: str
    className: str | None = None
    user: UserResponse

    class Config:
        from_attributes = True
        populate_by_name = True
