from datetime import datetime

from pydantic import BaseModel


class SchoolClassBase(BaseModel):
    name: str
    schoolId: str


class SchoolClassCreateRequest(SchoolClassBase):
    pass


class SchoolClassUpdateRequest(BaseModel):
    name: str | None = None


class SchoolClassResponse(SchoolClassBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
