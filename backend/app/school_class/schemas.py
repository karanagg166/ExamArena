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


class ClassTeacherResponse(BaseModel):
    id: str
    userId: str
    name: str = ""
    email: str = ""
    phoneNo: str = ""
    experience: int = 0
    department: str = ""
    subjects: list[str] = []
    qualifications: list[str] = []
    subjectTaught: str | None = None

    class Config:
        from_attributes = True


class SchoolClassResponse(SchoolClassBase):
    id: str
    schoolId: str
    teacherId: str | None = None
    joinCode: str
    nextRollNo: int
    createdAt: datetime
    updatedAt: datetime
    teachers: list[ClassTeacherResponse] = []

    class Config:
        from_attributes = True


class AssignStudentRequest(BaseModel):
    studentId: str


class AssignTeacherRequest(BaseModel):
    teacherId: str
