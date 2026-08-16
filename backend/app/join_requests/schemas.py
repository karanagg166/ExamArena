from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class JoinRequestCreate(BaseModel):
    """Internal request shape once a join code has been resolved to a class."""

    classId: str


class JoinByCodeRequest(BaseModel):
    joinCode: str = Field(min_length=4, max_length=16)


class JoinRequestDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    rollNo: str | None = None
    autoRollNo: bool = True

    @field_validator("rollNo")
    @classmethod
    def validate_numeric_roll_no(cls, v: str | None) -> str | None:
        if v is not None:
            v_str = str(v).strip()
            if not v_str:
                return None
            if not v_str.isdigit():
                raise ValueError("Roll number must contain numbers only.")
            if int(v_str) <= 0:
                raise ValueError("Roll number must be greater than 0.")
            return v_str
        return None


class JoinRequestResponse(BaseModel):
    id: str
    studentUserId: str
    classId: str
    className: str
    schoolId: str | None = None
    status: str
    requestedAt: datetime
    decidedAt: datetime | None = None
    studentName: str
    studentEmail: str

    class Config:
        from_attributes = True
