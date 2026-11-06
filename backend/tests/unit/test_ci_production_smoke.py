"""Offline regression tests for Exam Arena deployment smoke test script.

These unit tests mock HTTP calls and verify script logic, exit codes, and failure handling.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path
repo_root = Path(__file__).resolve().parents[3]
scripts_dir = repo_root / "scripts"
for p in (str(repo_root), str(scripts_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

import ci_production_smoke as smoke


@pytest.fixture(autouse=True)
def reset_smoke_state():
    smoke.RESULTS.clear()


def test_wait_for_frontend_success():
    with patch.object(smoke, "http", return_value=(200, {}, "<html><body>Exam Arena</body></html>")):
        smoke.wait_for_frontend()
    assert any(name == "Frontend Accessibility" and status == "PASS" for name, status, _ in smoke.RESULTS)


def test_wait_for_frontend_failure(monkeypatch):
    monkeypatch.setattr(smoke, "WAIT_SECONDS", 0.01)
    with patch.object(smoke, "http", return_value=(500, {}, "Server Error")), patch("time.sleep"):
        with pytest.raises(AssertionError, match="Frontend Accessibility"):
            smoke.wait_for_frontend()


def test_wait_for_api_health_success(monkeypatch):
    sha = "a" * 40
    monkeypatch.setattr(smoke, "EXPECTED_SHA", sha)
    payload = {"status": "ok", "service": "exam-arena-api", "git_commit": sha}
    with patch.object(smoke, "http", return_value=(200, {}, payload)):
        result = smoke.wait_for_api_health()
    assert result["status"] == "ok"
    assert any(name == "FastAPI Health" and status == "PASS" for name, status, _ in smoke.RESULTS)


def test_stale_api_revision_cannot_pass(monkeypatch):
    monkeypatch.setattr(smoke, "EXPECTED_SHA", "a" * 40)
    monkeypatch.setattr(smoke, "WAIT_SECONDS", 0.01)
    payload = {"status": "ok", "git_commit": "b" * 40}
    with patch.object(smoke, "http", return_value=(200, {}, payload)), patch("time.sleep"):
        with pytest.raises(AssertionError, match="different or unknown revision"):
            smoke.wait_for_api_health()


def test_missing_expected_revision_fails_before_http(monkeypatch):
    monkeypatch.setattr(smoke, "EXPECTED_SHA", "")
    with patch.object(smoke, "http") as http:
        assert smoke.main() == 1
        http.assert_not_called()


def test_check_infrastructure_readiness_success():
    payload = {"status": "ready", "database": "connected", "redis": "connected"}
    with patch.object(smoke, "http", return_value=(200, {}, payload)):
        smoke.check_infrastructure_readiness()
    assert any(name == "PostgreSQL Readiness" and status == "PASS" for name, status, _ in smoke.RESULTS)
    assert any(name == "Redis Readiness" and status == "PASS" for name, status, _ in smoke.RESULTS)


def test_check_worker_status_reports_blocked_on_503():
    payload = {
        "service": "exam-arena-worker",
        "worker_available": False,
        "detail": "No active worker detected",
    }
    with patch.object(smoke, "http", return_value=(503, {}, payload)):
        smoke.check_worker_status()
    assert any(name == "Worker Heartbeat" and status == "BLOCKED" for name, status, _ in smoke.RESULTS)


def test_check_auth_boundaries_enforces_401():
    with patch.object(smoke, "http", return_value=(401, {}, {"detail": "Not authenticated"})):
        smoke.check_auth_boundaries()
    assert any(name == "Exams Auth Boundary" and status == "PASS" for name, status, _ in smoke.RESULTS)
    assert any(name == "Token Boundary" and status == "PASS" for name, status, _ in smoke.RESULTS)
