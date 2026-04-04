from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr


class SchoolType(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    CHARTER = "CHARTER"
    INTERNATIONAL = "INTERNATIONAL"


# ─── Used when creating a school ─────────────────────────────────────────────


class SchoolCreateRequest(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    pincode: str
    schoolCode: str
    type: SchoolType = SchoolType.PUBLIC
    email: EmailStr | None = None
    website: str | None = None


class SchoolUpdateRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    schoolCode: str | None = None
    type: SchoolType | None = None
    email: EmailStr | None = None
    website: str | None = None


# ─── Used when returning a school ────────────────────────────────────────────


class SchoolResponse(BaseModel):
    id: str
    name: str
    createdBy: str
    address: str
    city: str
    state: str
    country: str
    pincode: str
    schoolCode: str
    type: SchoolType
    email: EmailStr | None = None
    website: str | None = None
    principalName: str | None = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


# ─── Used for filtering schools — only optional fields ───────────────────────


class SchoolFilterParams(BaseModel):
    name: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    school_code: str | None = None
    school_type: SchoolType | None = None
    email: EmailStr | None = None
    website: str | None = None
