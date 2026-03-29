from pydantic import BaseModel

from app.teachers.schemas import TeacherResponse


class PrincipalCreateRequest(BaseModel):
    """Request body for creating a principal profile."""

    schoolId: str | None = None
    experience: int


class PrincipalUpdate(BaseModel):
    experience: int | None = None
    schoolId: str | None = None


class PrincipalResponse(BaseModel):
    id: str
    teacherId: str
    schoolId: str | None = None
    experience: int
    teacher: TeacherResponse | None = None

    class Config:
        from_attributes = True
