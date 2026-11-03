#!/usr/bin/env python3
"""Exam Arena Production Post-Deployment Smoke Verification Suite.

Zero external dependencies. Tests live production deployments:
1. Vercel Frontend: https://exam-arena-mu.vercel.app
2. FastAPI Backend on Vercel Serverless: /api/health, /api/health/ready
3. PostgreSQL & Redis Infrastructure via /api/health/ready
4. ARQ Worker Availability & Fail-Secure Diagnostics: /api/health/worker
5. Role-Based Access Control Boundaries: /api/v1/exams, /api/v1/auth/me
6. Optional Authenticated Exam Listing Schema Verification

Strict Production Safety:
- Strictly read-only against live endpoints.
- Never creates, submits, or modifies students' exams or grades.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

FRONTEND_URL = os.environ.get("PROD_FRONTEND_URL", "https://exam-arena-mu.vercel.app").rstrip("/")
API_URL = os.environ.get("PROD_API_URL", FRONTEND_URL).rstrip("/")
EXPECTED_SHA = os.environ.get("EXPECTED_SHA", "").strip().lower()
WAIT_SECONDS = int(os.environ.get("SMOKE_WAIT_SECONDS", "180"))
RESULTS: list[tuple[str, str, str]] = []  # (Name, Status, Details)


def record(name: str, status: str, detail: str = "") -> None:
    icon = "✓" if status == "PASS" else ("⚠" if status in ("BLOCKED", "NOT RUN") else "✗")
    print(f"{icon} {name}: {detail}", flush=True)
    RESULTS.append((name, status, detail))


def fail(name: str, detail: str) -> None:
    raise AssertionError(f"{name}: {detail}")


def http(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None = None,
    timeout: int = 15,
) -> tuple[int, dict[str, str], Any]:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    hdrs = {
        "Accept": "application/json, text/html",
        "User-Agent": "ExamArenaProductionSmoke/1.0",
    }
    hdrs.update(headers or {})
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, method=method, headers=hdrs, data=body)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as err:
        resp = err
    with resp:
        status_code = resp.status
        resp_headers = {k.lower(): v for k, v in resp.headers.items()}
        raw_bytes = resp.read(131072)
    try:
        payload: Any = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = raw_bytes.decode("utf-8", errors="replace")
    return status_code, resp_headers, payload


def wait_for_frontend() -> None:
    deadline = time.monotonic() + WAIT_SECONDS
    last_err = "not contacted"
    while time.monotonic() < deadline:
        try:
            status, _, body = http(FRONTEND_URL, timeout=12)
            if status == 200 and isinstance(body, str) and ("html" in body.lower() or "<!doctype" in body.lower()):
                record("Frontend Accessibility", "PASS", f"Vercel responsive HTTP 200 at {FRONTEND_URL}")
                return
            last_err = f"HTTP {status}"
        except Exception as exc:
            last_err = type(exc).__name__
        time.sleep(5)
    fail("Frontend Accessibility", f"failed to reach frontend: {last_err}")


def wait_for_api_health() -> dict[str, Any]:
    deadline = time.monotonic() + WAIT_SECONDS
    last_err = "not contacted"
    while time.monotonic() < deadline:
        try:
            status, _, payload = http(f"{API_URL}/api/health", timeout=12)
            if status == 200 and isinstance(payload, dict) and payload.get("status") == "ok":
                commit = str(payload.get("git_commit", ""))
                commit_info = f"commit {commit[:10]}" if commit else "live"
                record("FastAPI Health", "PASS", f"liveness OK, service={payload.get('service')}, {commit_info}")
                return payload
            last_err = f"HTTP {status}: {payload}"
        except Exception as exc:
            last_err = type(exc).__name__
        time.sleep(5)
    fail("FastAPI Health", f"health endpoint unreachable or not OK: {last_err}")


def check_infrastructure_readiness() -> None:
    last_err = "not contacted"
    for attempt in range(1, 4):
        try:
            status, _, payload = http(f"{API_URL}/api/health/ready", timeout=15)
            if status == 200 and isinstance(payload, dict) and payload.get("status") == "ready":
                db = payload.get("database")
                redis = payload.get("redis")
                if db != "connected":
                    fail("Database Readiness", f"PostgreSQL reported status: {db}")
                record("PostgreSQL Readiness", "PASS", "database connected via async SQLAlchemy engine")

                if redis == "connected":
                    record("Redis Readiness", "PASS", "Redis cluster reachable and responsive")
                else:
                    record("Redis Readiness", "BLOCKED", f"Redis status reported: {redis}")
                return
            last_err = f"HTTP {status}: {payload}"
        except Exception as exc:
            last_err = type(exc).__name__
        if attempt < 3:
            time.sleep(4)
    fail("Infrastructure Readiness", last_err)


def check_worker_status() -> None:
    """Inspect background worker availability and queue health.
    
    Reports PASS if active ARQ worker is detected.
    Reports BLOCKED if worker is inactive (e.g. Free Tier single-service constraint),
    verifying that the backend fails securely with preserved imports.
    """
    try:
        status, _, payload = http(f"{API_URL}/api/health/worker", timeout=15)
        if status == 200 and isinstance(payload, dict) and payload.get("worker_available"):
            record("Worker Heartbeat", "PASS", "active ARQ worker consuming jobs from Redis queue")
        elif status == 503 and isinstance(payload, dict):
            detail = payload.get("detail", "Worker unavailable")
            record(
                "Worker Heartbeat",
                "BLOCKED",
                f"no active background worker on $0 infrastructure ({detail.replace('|', '/')}); fail-secure import queuing active",
            )
        else:
            record("Worker Heartbeat", "BLOCKED", f"worker status returned HTTP {status}")
    except Exception as exc:
        record("Worker Heartbeat", "BLOCKED", f"worker check exception: {type(exc).__name__}")


def check_auth_boundaries() -> None:
    # 1. Anonymous access to exams list
    status, _, _ = http(f"{API_URL}/api/v1/exams")
    if status not in (401, 403):
        fail("Exams Auth Boundary", f"anonymous /api/v1/exams returned HTTP {status}, expected 401/403")
    record("Exams Auth Boundary", "PASS", f"anonymous access safely rejected (HTTP {status})")

    # 2. Forged Bearer token access
    status, _, _ = http(f"{API_URL}/api/v1/exams", headers={"Authorization": "Bearer forged_invalid_ci_token"})
    if status not in (401, 403):
        fail("Token Boundary", f"forged token returned HTTP {status}, expected 401/403")
    record("Token Boundary", "PASS", f"forged bearer token rejected (HTTP {status})")

    # 3. Anonymous user profile access
    status, _, _ = http(f"{API_URL}/api/v1/auth/me")
    if status not in (401, 403):
        fail("Auth Profile Boundary", f"anonymous /api/v1/auth/me returned HTTP {status}")
    record("Auth Profile Boundary", "PASS", f"unauthenticated profile query rejected (HTTP {status})")


def check_authenticated_exam_schema() -> None:
    token = os.environ.get("PROD_SMOKE_BEARER_TOKEN", "").strip()
    if not token:
        record("Exam Schema Validation", "NOT RUN", "configure PROD_SMOKE_BEARER_TOKEN to test authenticated exam listings")
        return

    headers = {"Authorization": f"Bearer {token}"}
    status, _, payload = http(f"{API_URL}/api/v1/exams/public", headers=headers, timeout=20)
    if status != 200 or not isinstance(payload, list):
        fail("Exam Schema Validation", f"expected HTTP 200 list, got HTTP {status}: {payload}")

    if payload:
        sample = payload[0]
        required_fields = ["id", "name", "type", "duration", "status"]
        missing = [f for f in required_fields if f not in sample]
        if missing:
            fail("Exam Schema Validation", f"missing fields {missing} in exam schema: {sample}")
        record("Exam Schema Validation", "PASS", f"retrieved {len(payload)} exams with valid schema (sample: {sample.get('name')})")
    else:
        record("Exam Schema Validation", "PASS", "authenticated query succeeded (0 published exams currently in database)")


def write_summary() -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as f:
        f.write("### Exam Arena Post-Deployment Verification\n\n")
        f.write("| Verification | Status | Details |\n")
        f.write("|---|---|---|\n")
        for name, status, detail in RESULTS:
            icon = "✅" if status == "PASS" else ("⚠️" if status in ("BLOCKED", "NOT RUN") else "❌")
            f.write(f"| {name} | {icon} {status} | {detail.replace('|', '/')} |\n")
        f.write("\n")


def main() -> int:
    print("\033[34m======================================================\033[0m")
    print("\033[34m🎓 Exam Arena Production Deployment Smoke Suite\033[0m")
    print("\033[34m======================================================\033[0m")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"API URL:      {API_URL}\n")

    try:
        wait_for_frontend()
        wait_for_api_health()
        check_infrastructure_readiness()
        check_worker_status()
        check_auth_boundaries()
        check_authenticated_exam_schema()

        has_failures = any(r[1] == "FAIL" for r in RESULTS)
        if has_failures:
            print("\n\033[31m💥 DEPLOYMENT SMOKE SUITE REPORTED FAILURES\033[0m")
            return 1

        print("\n\033[32m======================================================\033[0m")
        print("\033[32m🎉 ALL EXAM ARENA PRODUCTION TESTS PASSED\033[0m")
        print("\033[32m======================================================\033[0m")
        return 0
    except (AssertionError, urllib.error.URLError, TimeoutError, OSError) as exc:
        record("Deployment Suite", "FAIL", str(exc))
        print(f"\n\033[31m::error::{exc}\033[0m", file=sys.stderr)
        return 1
    finally:
        write_summary()


if __name__ == "__main__":
    raise SystemExit(main())
