from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    timestamp: datetime
    actorId: str | None = None
    actorEmail: str | None = None
    actorRole: str | None = None
    action: str
    resourceType: str
    resourceId: str | None = None
    status: str
    requestId: str | None = None
    ipAddress: str | None = None
    userAgent: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, alias="metadata_")
