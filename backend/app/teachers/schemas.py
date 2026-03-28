from pydantic import BaseModel, field_validator
from app.users.schemas import UserResponse
import json


class TeacherCreateRequest(BaseModel):
    """What the frontend sends — no userId (injected from JWT)"""
    qualifications: list[str] = []   # stored as JSON string in DB column
    experience: int
    department: str
    subjects: list[str] = []         # stored as JSON string in DB column

    @property
    def qualification(self) -> str:
        """Serialize qualifications list → JSON string for DB storage"""
        return json.dumps(self.qualifications)

    @property
    def subjects_str(self) -> str:
        """Serialize subjects list → JSON string for DB storage"""
        return json.dumps(self.subjects)


class TeacherCreate(TeacherCreateRequest):
    """Internal use — includes userId injected server-side"""
    userId: str


class UserUpdateNested(BaseModel):
    name: str | None = None
    email: str | None = None
    phoneNo: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None


class TeacherUpdate(BaseModel):
    user: UserUpdateNested | None = None
    qualifications: list[str] | None = None
    experience: int | None = None
    department: str | None = None
    subjects: list[str] | None = None


class TeacherResponse(BaseModel):
    id: str
    userId: str
    qualifications: list[str] = []
    experience: int
    department: str
    subjects: list[str] = []
    user: UserResponse

    @field_validator("qualifications", "subjects", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        """DB stores JSON string → deserialize back to list on read"""
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, list) else [v]
            except Exception:
                return [v] if v else []
        return v or []

    class Config:
        from_attributes = True
