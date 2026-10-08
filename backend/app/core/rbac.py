"""Role-Based Access Control (RBAC) service using Casbin.

Provides centralized policy definition, enforcement, and FastAPI dependencies
for role authorization across all endpoints.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from functools import lru_cache
from typing import Any

import casbin
from fastapi import Cookie, Depends, HTTPException, status

logger = logging.getLogger(__name__)

# Inline default model definition as a fallback if configuration file is missing
RBAC_MODEL_CONF_TEXT = """
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && (r.obj == p.obj || p.obj == "*") && (r.act == p.act || p.act == "*")
"""

# Default RBAC policy rules: (Role, Resource/Object, Action)
DEFAULT_RBAC_POLICIES: list[tuple[str, str, str]] = [
    # ADMIN: Unrestricted access
    ("ADMIN", "*", "*"),
    # PRINCIPAL: Management of school, staff, classes, exams, audit logs
    ("PRINCIPAL", "dashboard", "*"),
    ("PRINCIPAL", "school", "*"),
    ("PRINCIPAL", "school_classes", "*"),
    ("PRINCIPAL", "teachers", "*"),
    ("PRINCIPAL", "students", "*"),
    ("PRINCIPAL", "exams", "*"),
    ("PRINCIPAL", "questions", "*"),
    ("PRINCIPAL", "sections", "*"),
    ("PRINCIPAL", "question_imports", "*"),
    ("PRINCIPAL", "answer_key_imports", "*"),
    ("PRINCIPAL", "join_requests", "*"),
    ("PRINCIPAL", "audit", "read"),
    ("PRINCIPAL", "notifications", "*"),
    ("PRINCIPAL", "attempts", "read"),
    ("PRINCIPAL", "profile", "*"),
    ("PRINCIPAL", "chat", "*"),
    ("PRINCIPAL", "grading", "*"),
    ("PRINCIPAL", "analytics", "*"),
    ("PRINCIPAL", "results", "*"),
    # TEACHER: Authoring exams/questions, managing assigned classes, student grading
    ("TEACHER", "dashboard", "*"),
    ("TEACHER", "exams", "*"),
    ("TEACHER", "questions", "*"),
    ("TEACHER", "sections", "*"),
    ("TEACHER", "question_imports", "*"),
    ("TEACHER", "answer_key_imports", "*"),
    ("TEACHER", "grading", "*"),
    ("TEACHER", "analytics", "*"),
    ("TEACHER", "results", "*"),
    ("TEACHER", "school_classes", "read"),
    ("TEACHER", "school_classes", "manage"),
    ("TEACHER", "students", "read"),
    ("TEACHER", "teachers", "read"),
    ("TEACHER", "join_requests", "*"),
    ("TEACHER", "school", "read"),
    ("TEACHER", "school", "join"),
    ("TEACHER", "attempts", "read"),
    ("TEACHER", "notifications", "*"),
    ("TEACHER", "profile", "*"),
    ("TEACHER", "chat", "*"),
    # STUDENT: Taking exams, viewing own attempts and enrolled classes
    ("STUDENT", "dashboard", "*"),
    ("STUDENT", "exams", "read"),
    ("STUDENT", "exams", "search"),
    ("STUDENT", "attempts", "start"),
    ("STUDENT", "attempts", "submit"),
    ("STUDENT", "attempts", "read_own"),
    ("STUDENT", "attempts", "proctoring_violation"),
    ("STUDENT", "analytics", "read_own"),
    ("STUDENT", "results", "read_own"),
    ("STUDENT", "school_classes", "read"),
    ("STUDENT", "school_classes", "join"),
    ("STUDENT", "students", "read"),
    ("STUDENT", "teachers", "read"),
    ("STUDENT", "school", "read"),
    ("STUDENT", "join_requests", "create"),
    ("STUDENT", "join_requests", "read_own"),
    ("STUDENT", "notifications", "*"),
    ("STUDENT", "profile", "*"),
    ("STUDENT", "chat", "*"),
]


def _build_model() -> casbin.Model:
    """Builds the Casbin Model from file or fallback string."""
    model = casbin.Model()
    conf_path = os.path.join(os.path.dirname(__file__), "rbac_model.conf")
    if os.path.exists(conf_path):
        model.load_model(conf_path)
    else:
        model.load_model_from_text(RBAC_MODEL_CONF_TEXT.strip())
    return model


@lru_cache(maxsize=1)
def get_casbin_enforcer() -> casbin.Enforcer:
    """Returns a cached singleton instance of the Casbin Enforcer."""
    model = _build_model()
    # Using memory adapter with explicit policy initialization
    adapter = casbin.persist.adapters.FileAdapter("") if False else None
    enforcer = casbin.Enforcer(model, adapter)

    for sub, obj, act in DEFAULT_RBAC_POLICIES:
        enforcer.add_policy(
            sub.strip().upper(), obj.strip().lower(), act.strip().lower()
        )

    logger.info(
        "🛡️ Casbin RBAC enforcer initialized with %d policies",
        len(DEFAULT_RBAC_POLICIES),
    )
    return enforcer


def check_rbac_permission(sub: str, obj: str, act: str) -> bool:
    """Evaluates whether a subject (role) is authorized for action on object."""
    if not sub:
        return False
    enforcer = get_casbin_enforcer()
    subject = str(sub).strip().upper()
    resource = str(obj).strip().lower()
    action = str(act).strip().lower()
    return bool(enforcer.enforce(subject, resource, action))


def enforce_rbac_permission(
    user_role: Any, obj: str, act: str, custom_detail: str | None = None
) -> None:
    """Validates user permission using Casbin and raises HTTP 403 Forbidden if denied."""
    role_str = user_role.value if hasattr(user_role, "value") else str(user_role or "")
    if not check_rbac_permission(role_str, obj, act):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=custom_detail
            or f"Forbidden: Role '{role_str}' cannot perform '{act}' on '{obj}'",
        )


def require_rbac_permission(obj: str, act: str) -> Callable[..., Any]:
    """FastAPI dependency factory to enforce Casbin permissions on endpoint routes."""

    async def _rbac_dependency(
        access_token: str = Cookie(None),
    ) -> Any:
        from app.api.deps import get_current_user

        user = await get_current_user(access_token)
        enforce_rbac_permission(user.role, obj, act)
        return user

    return _rbac_dependency
