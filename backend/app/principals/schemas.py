from pydantic import BaseModel
from app.users.schemas import UserResponse
from app.teachers.schemas import TeacherResponse


class PrincipalCreateRequest(BaseModel):
    """Frontend sends schoolId + experience. Teacher record must already exist."""
    schoolId: str
    experience: int


class PrincipalUpdate(BaseModel):
    experience: int | None = None


class PrincipalResponse(BaseModel):
    id: str
    teacherId: str | None = None
    schoolId: str
    experience: int

    class Config:
        from_attributes = True
