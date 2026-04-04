from datetime import datetime

from pydantic import BaseModel


class SchoolClassBase(BaseModel):
    name: str
    year: str
    section: str = "A"


class SchoolClassCreateRequest(SchoolClassBase):
    pass


class SchoolClassUpdateRequest(BaseModel):
    name: str | None = None
    year: str | None = None
    section: str | None = None
    teacherId: str | None = None


class SchoolClassResponse(SchoolClassBase):
    id: str
    schoolId: str
    teacherId: str | None = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
