from contextvars import ContextVar
from typing import Any

request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)
client_ip_ctx: ContextVar[str | None] = ContextVar("client_ip_ctx", default=None)
user_agent_ctx: ContextVar[str | None] = ContextVar("user_agent_ctx", default=None)
current_actor_ctx: ContextVar[dict[str, Any] | None] = ContextVar(
    "current_actor_ctx", default=None
)


def get_current_request_id() -> str | None:
    return request_id_ctx.get()


def set_current_request_id(request_id: str | None) -> None:
    request_id_ctx.set(request_id)


def get_current_client_ip() -> str | None:
    return client_ip_ctx.get()


def set_current_client_ip(ip: str | None) -> None:
    client_ip_ctx.set(ip)


def get_current_user_agent() -> str | None:
    return user_agent_ctx.get()


def set_current_user_agent(ua: str | None) -> None:
    user_agent_ctx.set(ua)


def get_current_actor() -> dict[str, Any] | None:
    return current_actor_ctx.get()


def set_current_actor(
    actor_id: str | None, email: str | None, role: str | None
) -> None:
    current_actor_ctx.set({"id": actor_id, "email": email, "role": role})


def clear_audit_context() -> None:
    request_id_ctx.set(None)
    client_ip_ctx.set(None)
    user_agent_ctx.set(None)
    current_actor_ctx.set(None)
