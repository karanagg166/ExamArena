from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from enum import Enum
from typing import Optional


class SchoolType(str, Enum):
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
    email: Optional[EmailStr] = None
    website: Optional[str] = None


class SchoolUpdateRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    schoolCode: Optional[str] = None
    type: Optional[SchoolType] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None


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
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


# ─── Used for filtering schools — only optional fields ───────────────────────

class SchoolFilterParams(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    school_code: Optional[str] = None
    school_type: Optional[SchoolType] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None