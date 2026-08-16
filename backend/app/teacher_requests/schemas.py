from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.core.models import Subject


class TeacherClassJoinRequestCreate(BaseModel):
    classId: str
    subject: Subject | None = None


class TeacherClassJoinRequestDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]


class TeacherClassJoinRequestResponse(BaseModel):
    id: str
    teacherId: str
    teacherName: str
    teacherEmail: str
    classId: str
    className: str
    schoolId: str
    subject: str | None = None
    status: str
    requestedAt: datetime
    decidedAt: datetime | None = None
    decidedBy: str | None = None

    class Config:
        from_attributes = True


class TeacherSchoolJoinRequestCreate(BaseModel):
    schoolId: str


class TeacherSchoolJoinRequestDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]


class TeacherSchoolJoinRequestResponse(BaseModel):
    id: str
    teacherId: str
    teacherName: str
    teacherEmail: str
    teacherDepartment: str | None = None
    schoolId: str
    schoolName: str
    status: str
    requestedAt: datetime
    decidedAt: datetime | None = None
    decidedBy: str | None = None

    class Config:
        from_attributes = True


class TeacherAssignClassesRequest(BaseModel):
    teacherId: str
    classIds: list[str]
    subject: Subject | None = None


class TeacherAssignClassesResponse(BaseModel):
    teacherId: str
    classIds: list[str]
    assignedCount: int
    message: str
