from pyndantic import BaseModel, EmailStr, Field
from app.users.schemas import UserResponse

class SchoolBase(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    pincode: str


class SchoolCreate(SchoolBase):
    pass