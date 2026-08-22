"""Unit tests for Casbin Role-Based Access Control (RBAC) engine."""

import pytest
from fastapi import HTTPException

from app.core.rbac import (
    check_rbac_permission,
    enforce_rbac_permission,
    get_casbin_enforcer,
)


class TestCasbinRBAC:
    """Tests for Casbin policy enforcement across roles and resources."""

    def test_enforcer_initialization(self):
        enforcer = get_casbin_enforcer()
        assert enforcer is not None

    def test_admin_full_access(self):
        assert check_rbac_permission("ADMIN", "exams", "create") is True
        assert check_rbac_permission("ADMIN", "schools", "delete") is True
        assert check_rbac_permission("ADMIN", "audit", "read") is True
        assert check_rbac_permission("ADMIN", "anything", "any_action") is True

    def test_principal_permissions(self):
        assert check_rbac_permission("PRINCIPAL", "school", "create") is True
        assert check_rbac_permission("PRINCIPAL", "school_classes", "create") is True
        assert check_rbac_permission("PRINCIPAL", "exams", "create") is True
        assert check_rbac_permission("PRINCIPAL", "audit", "read") is True
        assert check_rbac_permission("PRINCIPAL", "attempts", "start") is False

    def test_teacher_permissions(self):
        assert check_rbac_permission("TEACHER", "exams", "create") is True
        assert check_rbac_permission("TEACHER", "exams", "update") is True
        assert check_rbac_permission("TEACHER", "questions", "create") is True
        assert check_rbac_permission("TEACHER", "school_classes", "read") is True
        assert check_rbac_permission("TEACHER", "school_classes", "manage") is True
        # Teachers cannot create schools or read system audit logs
        assert check_rbac_permission("TEACHER", "school", "create") is False
        assert check_rbac_permission("TEACHER", "audit", "read") is False
        assert check_rbac_permission("TEACHER", "attempts", "start") is False

    def test_student_permissions(self):
        assert check_rbac_permission("STUDENT", "exams", "read") is True
        assert check_rbac_permission("STUDENT", "exams", "search") is True
        assert check_rbac_permission("STUDENT", "attempts", "start") is True
        assert check_rbac_permission("STUDENT", "attempts", "submit") is True
        assert check_rbac_permission("STUDENT", "school_classes", "join") is True
        # Students cannot create exams or manage schools
        assert check_rbac_permission("STUDENT", "exams", "create") is False
        assert check_rbac_permission("STUDENT", "school", "create") is False
        assert check_rbac_permission("STUDENT", "questions", "create") is False
        assert check_rbac_permission("STUDENT", "audit", "read") is False

    def test_empty_or_unknown_role(self):
        assert check_rbac_permission("", "exams", "read") is False
        assert check_rbac_permission("UNKNOWN_ROLE", "exams", "read") is False

    def test_enforce_rbac_permission_raises_403(self):
        # Student cannot create exams -> raises 403
        with pytest.raises(HTTPException) as exc_info:
            enforce_rbac_permission("STUDENT", "exams", "create")
        assert exc_info.value.status_code == 403
        assert "Forbidden" in exc_info.value.detail

        # Admin creating exams -> does not raise
        enforce_rbac_permission("ADMIN", "exams", "create")
