import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.audit.context import (
    get_current_actor,
    get_current_client_ip,
    get_current_request_id,
    get_current_user_agent,
)
from app.audit.sanitizer import sanitize_metadata
from app.core.models import AuditLog

logger = logging.getLogger("exam_arena.audit")


async def record_audit_event(
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    actor_id: str | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    status: str = "SUCCESS",
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    session: AsyncSession | None = None,
) -> AuditLog:
    """
    Centralized, secure function for recording persistent audit events.
    Derives context attributes (request ID, IP, actor) automatically when omitted.
    """
    # 1. Derive contextual metadata from thread-local / async context if not provided
    req_id = request_id or get_current_request_id()
    ip = ip_address or get_current_client_ip()
    ua = user_agent or get_current_user_agent()

    if actor_id is None or actor_email is None or actor_role is None:
        ctx_actor = get_current_actor()
        if ctx_actor:
            actor_id = actor_id or ctx_actor.get("id")
            actor_email = actor_email or ctx_actor.get("email")
            actor_role = actor_role or ctx_actor.get("role")

    # 2. Sanitize any metadata to strictly scrub secrets, tokens, passwords
    cleaned_metadata = sanitize_metadata(metadata) if metadata else None

    # 3. Construct AuditLog database record
    audit_entry = AuditLog(
        action=str(action),
        resourceType=str(resource_type),
        resourceId=str(resource_id) if resource_id is not None else None,
        actorId=str(actor_id) if actor_id is not None else None,
        actorEmail=str(actor_email) if actor_email is not None else None,
        actorRole=str(actor_role) if actor_role is not None else None,
        status=str(status),
        requestId=req_id,
        ipAddress=ip,
        userAgent=ua,
        metadata_=cleaned_metadata,
        timestamp=datetime.now(UTC),
    )

    # 4. Persist to database
    try:
        if session:
            session.add(audit_entry)
            await session.flush()
        else:
            async with db.get_session() as standalone_session:
                standalone_session.add(audit_entry)
                await standalone_session.commit()
    except Exception as exc:
        logger.exception(
            "Failed to write persistent audit log action=%s resource=%s error=%s",
            action,
            resource_type,
            exc,
        )

    # 5. Standard structured log output for log collectors
    logger.info(
        "AUDIT [%s] action=%s resource=%s:%s actor=%s(%s) req_id=%s ip=%s",
        status,
        action,
        resource_type,
        resource_id or "-",
        actor_email or actor_id or "ANONYMOUS",
        actor_role or "-",
        req_id or "-",
        ip or "-",
    )

    return audit_entry


async def get_audit_logs(
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession | None = None,
) -> list[AuditLog]:
    """Retrieve audit logs with optional filters and pagination."""
    capped_limit = min(max(1, limit), 200)

    async def _query(s: AsyncSession) -> list[AuditLog]:
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resourceType == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLog.resourceId == resource_id)
        if actor_id:
            stmt = stmt.where(AuditLog.actorId == actor_id)
        if status:
            stmt = stmt.where(AuditLog.status == status)

        stmt = (
            stmt.order_by(desc(AuditLog.timestamp)).offset(offset).limit(capped_limit)
        )
        res = await s.execute(stmt)
        return list(res.scalars().all())

    if session:
        return await _query(session)
    async with db.get_session() as s:
        return await _query(s)
