from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.audit.schemas import AuditLogResponse
from app.audit.service import get_audit_logs
from app.core.models import Role
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    action: str | None = Query(None, description="Filter by action name"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    actor_id: str | None = Query(None, description="Filter by actor ID"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by result status"
    ),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Retrieve persistent security and business audit logs.
    Restricted to ADMIN and PRINCIPAL roles.
    """
    if current_user.role not in (Role.ADMIN, Role.PRINCIPAL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and principals can view audit logs.",
        )

    logs = await get_audit_logs(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return [AuditLogResponse.model_validate(log) for log in logs]
