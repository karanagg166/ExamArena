from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    phoneNo: str
    pincode: str
    password: str
    role: str
    city: str
    state: str
    country: str


class UserResponse(BaseModel):
    email: EmailStr
    name: str
    phoneNo: str
    pincode: str
    role: str
    city: str
    state: str
    country: str

    class Config:
        from_attributes = True  # for ORM (Prisma/SQLAlchemy)