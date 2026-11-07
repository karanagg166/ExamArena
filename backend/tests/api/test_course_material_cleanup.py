"""Authenticated cleanup receipts retain tenant isolation after local deletion."""

import httpx
import pytest

from tests.api import test_course_materials_api as material_support

setup_schools = material_support.setup_schools
mock_search_sphere_key = material_support.mock_search_sphere_key
_async_client = httpx.AsyncClient


def upstream(monkeypatch, *, value=None, status=200, failure=None):
    captured = []

    def handle(request):
        captured.append(request)
        if failure:
            raise failure("PRIVATE SYNTHETIC DIAGNOSTIC")
        return httpx.Response(status, json=value)

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: _async_client(transport=httpx.MockTransport(handle), **kw),
    )
    return captured


def receipt(**overrides):
    return {
        "document_id": "synthetic-material",
        "status": "complete",
        "vectors_remaining": 0,
        "derived_objects_remaining": 0,
        "object_deleted": True,
        **overrides,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("state,deleted", [("pending", False), ("complete", True)])
async def test_staff_reads_validated_receipt_without_local_metadata(
    auth_client_factory, setup_schools, monkeypatch, state, deleted
):
    calls = upstream(
        monkeypatch,
        value=receipt(
            status=state,
            object_deleted=deleted,
            storage_key="PRIVATE STORAGE",
            diagnostic="PRIVATE DIAGNOSTIC",
        ),
    )
    client = await auth_client_factory(setup_schools["teacher_a_user"])
    response = await client.get(
        "/api/v1/course-materials/synthetic-material/cleanup",
        headers={"X-Tenant-ID": "school_forged"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == receipt(status=state, object_deleted=deleted)
    assert len(calls) == 1
    assert calls[0].headers["x-tenant-id"] == "school_" + setup_schools["school_a"].id
    assert calls[0].url.path == "/api/v1/documents/synthetic-material/cleanup"
    assert calls[0].extensions["timeout"]["read"] == 10
    assert "PRIVATE" not in response.text and "ss_live" not in response.text


@pytest.mark.asyncio
async def test_student_cannot_query_management_cleanup(
    auth_client_factory, setup_schools, monkeypatch
):
    calls = upstream(monkeypatch, value=receipt())
    client = await auth_client_factory(setup_schools["student_a_user"])
    response = await client.get("/api/v1/course-materials/synthetic-material/cleanup")
    assert response.status_code == 403 and calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [403, 404, 503])
async def test_scope_denial_and_outage_cannot_verify_cleanup(
    auth_client_factory, setup_schools, monkeypatch, status
):
    calls = upstream(
        monkeypatch,
        status=status,
        value={"detail": "PRIVATE DIAGNOSTIC ss_live_do_not_expose"},
    )
    client = await auth_client_factory(setup_schools["teacher_a_user"])
    response = await client.get("/api/v1/course-materials/synthetic-material/cleanup")
    assert response.status_code == (404 if status in {403, 404} else 503)
    assert len(calls) == 1
    assert "PRIVATE" not in response.text and "ss_live" not in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value",
    [
        {},
        [],
        receipt(document_id="other-document"),
        receipt(vectors_remaining=1),
        receipt(derived_objects_remaining=1),
        receipt(object_deleted=False),
        receipt(vectors_remaining="0"),
        receipt(vectors_remaining=True),
        receipt(status="unknown"),
    ],
)
async def test_malformed_or_contradictory_receipts_are_unverified(
    auth_client_factory, setup_schools, monkeypatch, value
):
    upstream(monkeypatch, value=value)
    client = await auth_client_factory(setup_schools["teacher_a_user"])
    response = await client.get("/api/v1/course-materials/synthetic-material/cleanup")
    assert response.status_code == 503
    assert "vectors_remaining" not in response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [httpx.ReadTimeout, httpx.ConnectError])
async def test_cleanup_network_failure_is_bounded_without_retries(
    auth_client_factory, setup_schools, monkeypatch, failure
):
    calls = upstream(monkeypatch, failure=failure)
    client = await auth_client_factory(setup_schools["teacher_a_user"])
    response = await client.get("/api/v1/course-materials/synthetic-material/cleanup")
    assert response.status_code == 503 and len(calls) == 1
    assert "PRIVATE" not in response.text


@pytest.mark.asyncio
async def test_other_school_gets_only_its_own_delegation(
    auth_client_factory, setup_schools, monkeypatch
):
    calls = upstream(
        monkeypatch, status=404, value={"detail": "No receipt in this tenant"}
    )
    client = await auth_client_factory(setup_schools["teacher_b_user"])
    response = await client.get(
        "/api/v1/course-materials/synthetic-material/cleanup",
        headers={"X-Tenant-ID": "school_" + setup_schools["school_a"].id},
    )
    assert response.status_code == 404
    assert calls[0].headers["x-tenant-id"] == "school_" + setup_schools["school_b"].id
