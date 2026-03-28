from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    """Request body for login"""

    email: EmailStr
    password: str


class Roles(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PRINCIPAL = "PRINCIPAL"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


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
    dateOfBirth: datetime
    role: Roles


class UserResponse(BaseModel):
    """User data in response"""

    id: str
    email: str
    name: str
    phoneNo: str
    pincode: str
    city: str
    state: str
    dateOfBirth: datetime
    country: str
    role: Roles

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phoneNo: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    dateOfBirth: datetime | None = None
    role: Roles | None = None
    password: str | None = None
