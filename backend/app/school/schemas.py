from pydantic import BaseModel
from datetime import datetime

# 1. The Blueprint (What the frontend user fills out)
class SchoolBase(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    pincode: str
    createdBy: str # This will be injected in the backend based on the authenticated user.
    # User provides this now! Kept as string to prevent dropping leading zeros.
    schoolCode: str 

# 2. Creating a School (POST)
# Note: createdBy is NOT included here — it is injected server-side from the JWT token
class SchoolCreateRequest(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    pincode: str
    schoolCode: str

# 3. Updating a School (PATCH)
class SchoolUpdateRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    schoolCode: str | None = None
# 4. What the API sends back to the frontend
class SchoolResponse(SchoolBase):
    id: str
    createdAt: datetime 
    updatedAt: datetime

    class Config:
        from_attributes = True