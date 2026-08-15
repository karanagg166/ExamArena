from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class JoinRequestCreate(BaseModel):
    """Internal request shape once a join code has been resolved to a class."""

    classId: str


class JoinByCodeRequest(BaseModel):
    joinCode: str = Field(min_length=4, max_length=16)


class JoinRequestDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]


class JoinRequestResponse(BaseModel):
    id: str
    studentUserId: str
    classId: str
    className: str
    status: str
    requestedAt: datetime
    decidedAt: datetime | None = None
    studentName: str
    studentEmail: str

    class Config:
        from_attributes = True
