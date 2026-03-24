from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.users.schemas import UserResponse

class StudentBase(BaseModel):
    rollNo: str
    dob: datetime
    class_: str = Field(alias="class")  # Map 'class' from DB to 'class_' in Python
    parentName: str
    parentEmail: EmailStr

class StudentCreate(StudentBase):
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
    class_: str | None = None
    parentName: str | None = None
    parentEmail: EmailStr | None = None

class StudentResponse(StudentBase):
    id: str
    userId: str
    user: UserResponse
    
    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both 'class' and 'class_' as field names
