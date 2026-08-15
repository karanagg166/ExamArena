import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


def normalize_indian_phone(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if not v:
        return v
    # If 10 digits provided without prefix, normalize to +91
    if re.match(r"^\d{10}$", v):
        return f"+91{v}"
    if not re.match(r"^\+91\d{10}$", v):
        raise ValueError(
            "Phone number must start with +91 followed by exactly 10 digits"
        )
    return v


class LoginRequest(BaseModel):
    """Request body for login"""

    email: EmailStr
    password: str


class Roles(StrEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PRINCIPAL = "PRINCIPAL"
    ADMIN = "ADMIN"


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

    @field_validator("phoneNo", mode="before")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_indian_phone(v) or v


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

    @field_validator("phoneNo", mode="before")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return normalize_indian_phone(v)


class ChangePasswordRequest(BaseModel):
    """Request body for changing user password"""

    currentPassword: str
    newPassword: str
