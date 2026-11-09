from pydantic import BaseModel, field_validator

from app.teachers.schemas import TeacherResponse


class PrincipalCreateRequest(BaseModel):
    """Request body for creating a principal profile."""

    schoolId: str
    experience: int


class PrincipalUpdate(BaseModel):
    experience: int | None = None
    schoolId: str | None = None


class PrincipalProfileUpdate(PrincipalUpdate):
    """Self-service fields; school creation uses the trusted internal payload."""

    @field_validator("schoolId")
    @classmethod
    def reject_self_service_school_change(cls, value):
        raise ValueError("Principal school changes require authorized administration.")


class PrincipalResponse(BaseModel):
    id: str
    teacherId: str
    schoolId: str | None = None
    experience: int
    teacher: TeacherResponse | None = None

    class Config:
        from_attributes = True
