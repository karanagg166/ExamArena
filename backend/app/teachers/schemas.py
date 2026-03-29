import json

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.users.schemas import UserResponse


class TeacherCreateRequest(BaseModel):
    """What the frontend sends — no userId (injected from JWT)"""

    qualifications: list[str] = []  # stored as JSON string in DB column
    experience: int
    department: str
    subjects: list[str] = []  # stored as JSON string in DB column

    @property
    def qualification(self) -> str:
        """Serialize qualifications list → JSON string for DB storage"""
        return json.dumps(self.qualifications)

    @property
    def subjects_str(self) -> str:
        """Serialize subjects list → JSON string for DB storage"""
        return json.dumps(self.subjects)

    @model_validator(mode="before")
    @classmethod
    def support_singular_qualification_field(cls, data):
        if (
            isinstance(data, dict)
            and "qualifications" not in data
            and "qualification" in data
        ):
            singular = data.get("qualification")
            if isinstance(singular, str):
                data["qualifications"] = [
                    item.strip() for item in singular.split(",") if item.strip()
                ]
            elif isinstance(singular, list):
                data["qualifications"] = singular
        return data


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

    @model_validator(mode="before")
    @classmethod
    def support_singular_qualification_field(cls, data):
        if (
            isinstance(data, dict)
            and "qualifications" not in data
            and "qualification" in data
        ):
            singular = data.get("qualification")
            if isinstance(singular, str):
                data["qualifications"] = [
                    item.strip() for item in singular.split(",") if item.strip()
                ]
            elif isinstance(singular, list):
                data["qualifications"] = singular
        return data


class TeacherResponse(BaseModel):
    id: str
    userId: str
    qualifications: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("qualifications", "qualification"),
    )
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


class TeacherListItemResponse(BaseModel):
    id: str
    name: str
    email: str
    phoneNo: str
    experience: int
    qualifications: list[str] = []
    department: str
    subjects: list[str] = []


class TeacherFilterParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    email: str | None = None
    phone_no: str | None = Field(
        default=None,
        validation_alias=AliasChoices("phone_no", "phoneNo"),
        serialization_alias="phoneNo",
    )
    department: str | None = None
    subject: str | None = None
    qualification: str | None = None
    min_experience: int | None = Field(
        default=None,
        validation_alias=AliasChoices("min_experience", "minExperience"),
        serialization_alias="minExperience",
    )
    max_experience: int | None = Field(
        default=None,
        validation_alias=AliasChoices("max_experience", "maxExperience"),
        serialization_alias="maxExperience",
    )


class TeacherJoinSchoolRequest(BaseModel):
    school_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("school_id", "schoolId"),
        serialization_alias="schoolId",
    )
