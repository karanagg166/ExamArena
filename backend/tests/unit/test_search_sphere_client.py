"""Unit tests for SearchSphereClient with HTTP mocking and error boundaries."""

import json
import pytest
import httpx

from app.audit.context import clear_audit_context, set_current_request_id
from app.integrations.search_sphere.client import SearchSphereClient
from app.integrations.search_sphere.exceptions import (
    SearchSphereAuthenticationError,
    SearchSphereAuthorizationError,
    SearchSphereConfigurationError,
    SearchSphereConflictError,
    SearchSphereNotFoundError,
    SearchSphereTimeoutError,
    SearchSphereUnavailableError,
    SearchSphereValidationError,
)


@pytest.fixture(autouse=True)
def clean_audit():
    clear_audit_context()
    yield
    clear_audit_context()


_orig_async_client = httpx.AsyncClient


def mock_async_client(monkeypatch, transport: httpx.MockTransport):
    def _factory(**kwargs):
        kwargs["transport"] = transport
        return _orig_async_client(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _factory)


@pytest.mark.asyncio
async def test_client_configuration_error_missing_key():
    client = SearchSphereClient(base_url="http://mock-ss:8000", api_key="")
    with pytest.raises(SearchSphereConfigurationError, match="SEARCH_SPHERE_API_KEY is not configured"):
        await client.get_collection("coll_1", tenant_id="school_1")


@pytest.mark.asyncio
async def test_client_configuration_error_missing_url():
    client = SearchSphereClient(base_url="", api_key="ss_live_valid_key")
    with pytest.raises(SearchSphereConfigurationError, match="SEARCH_SPHERE_URL is not configured"):
        await client.get_collection("coll_1", tenant_id="school_1")


@pytest.mark.asyncio
async def test_client_request_headers_and_correlation(monkeypatch):
    captured_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"id": "coll_science", "name": "Science"})

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_test_api_key_12345",
        client_id="exam_arena",
        timeout_seconds=5.0,
    )

    set_current_request_id("req_trace_98765")

    res = await client.get_collection(collection_id="coll_science", tenant_id="school_sch_101")
    assert res["id"] == "coll_science"
    assert len(captured_requests) == 1

    req = captured_requests[0]
    assert req.headers["authorization"] == "Bearer ss_live_test_api_key_12345"
    assert req.headers["x-client-id"] == "exam_arena"
    assert req.headers["x-tenant-id"] == "school_sch_101"
    assert req.headers["x-request-id"] == "req_trace_98765"


@pytest.mark.asyncio
async def test_client_error_mappings(monkeypatch):
    status_to_test = [
        (401, SearchSphereAuthenticationError),
        (403, SearchSphereAuthorizationError),
        (404, SearchSphereNotFoundError),
        (409, SearchSphereConflictError),
        (400, SearchSphereValidationError),
        (422, SearchSphereValidationError),
        (500, SearchSphereUnavailableError),
        (503, SearchSphereUnavailableError),
    ]

    for status_code, expected_exc in status_to_test:
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code,
                json={"detail": f"Upstream error for {status_code}"},
            )

        transport = httpx.MockTransport(mock_handler)
        mock_async_client(monkeypatch, transport)

        client = SearchSphereClient(
            base_url="http://mock-ss:8000",
            api_key="ss_live_secret_key",
            client_id="exam_arena",
        )

        with pytest.raises(expected_exc) as exc_info:
            await client.get_collection("coll_test", tenant_id="school_1")

        err_msg = str(exc_info.value)
        assert "ss_live_secret_key" not in err_msg


@pytest.mark.asyncio
async def test_client_timeout_handling(monkeypatch):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out")

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    with pytest.raises(SearchSphereTimeoutError, match="Timed out"):
        await client.get_collection("coll_test", tenant_id="school_1")


@pytest.mark.asyncio
async def test_client_network_unavailable_handling(monkeypatch):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    with pytest.raises(SearchSphereUnavailableError, match="Unable to connect"):
        await client.get_collection("coll_test", tenant_id="school_1")


@pytest.mark.asyncio
async def test_client_ensure_collection_conflict_resolves_via_get(monkeypatch):
    calls: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.method == "POST":
            return httpx.Response(409, json={"detail": "Collection already exists"})
        return httpx.Response(200, json={"collection_id": "c_chem", "name": "Chemistry"})

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    res = await client.ensure_collection(
        collection_id="c_chem",
        name="Chemistry",
        tenant_id="school_alpha",
    )
    assert res["name"] == "Chemistry"
    assert calls == [
        "POST /api/v1/collections",
        "GET /api/v1/collections/c_chem",
    ]


@pytest.mark.asyncio
async def test_client_upload_and_register_document(monkeypatch):
    captured_routes: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_routes.append(request.url.path)
        if request.url.path == "/api/v1/documents/upload":
            return httpx.Response(
                201,
                json={
                    "storage_key": "docs/exam_arena/school_1/c_1/mat_1/notes.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024,
                },
            )
        if request.url.path == "/api/v1/documents":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["external_document_id"] == "mat_1"
            assert payload["storage_key"] == "docs/exam_arena/school_1/c_1/mat_1/notes.pdf"
            return httpx.Response(
                202,
                json={
                    "id": "ss_doc_999",
                    "client_id": "exam_arena",
                    "tenant_id": "school_1",
                    "external_document_id": "mat_1",
                    "status": "PROCESSING",
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    up_res = await client.upload_file(
        file_bytes=b"%PDF-1.4 dummy",
        filename="notes.pdf",
        content_type="application/pdf",
        document_id="mat_1",
        collection_id="c_1",
        tenant_id="school_1",
    )
    assert up_res["storage_key"] == "docs/exam_arena/school_1/c_1/mat_1/notes.pdf"

    reg_res = await client.register_document(
        external_document_id="mat_1",
        storage_key=up_res["storage_key"],
        file_name="notes.pdf",
        mime_type="application/pdf",
        file_size=1024,
        collection_id="c_1",
        owner_subject_id="user_usr_1",
        document_type="TEACHER_NOTES",
        metadata={"course": "physics"},
        tenant_id="school_1",
    )
    assert reg_res["id"] == "ss_doc_999"
    assert reg_res["status"] == "PROCESSING"


@pytest.mark.asyncio
async def test_client_search_forwarding(monkeypatch):
    captured_payloads: list[dict] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        captured_payloads.append(payload)
        return httpx.Response(
            200,
            json={
                "query": payload["query"],
                "total": 1,
                "results": [
                    {
                        "chunk_id": "chk_1",
                        "document_id": "ss_doc_999",
                        "text": "Snell's Law defines refraction",
                        "score": 0.88,
                        "rank": 1,
                        "start_page": 5,
                        "end_page": 5,
                    }
                ],
                "duration_ms": 15.2,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    res = await client.search(
        query="What is refraction?",
        collection_id="subject_science",
        limit=5,
        tenant_id="school_sch_1",
    )
    assert res["total"] == 1
    assert res["results"][0]["text"] == "Snell's Law defines refraction"
    assert captured_payloads[0]["query"] == "What is refraction?"
    assert captured_payloads[0]["collection_id"] == "subject_science"
    assert captured_payloads[0]["limit"] == 5


@pytest.mark.asyncio
async def test_client_delete_collection(monkeypatch):
    captured_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"success": True, "message": "Collection deleted"})

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    deleted = await client.delete_collection(
        collection_id="subject_maths",
        tenant_id="school_sch_1",
    )
    assert deleted is True
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.method == "DELETE"
    assert req.url.path == "/api/v1/collections/subject_maths"
    assert req.headers["x-tenant-id"] == "school_sch_1"
    assert req.headers["authorization"] == "Bearer ss_live_secret_key"
    assert req.headers["x-client-id"] == "exam_arena"


@pytest.mark.asyncio
async def test_client_generate_answer_forwarding(monkeypatch):
    captured_payloads: list[dict] = []
    captured_headers: list[httpx.Headers] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(request.headers)
        payload = json.loads(request.content.decode("utf-8"))
        captured_payloads.append(payload)
        return httpx.Response(
            200,
            json={
                "answer": "Total internal reflection occurs when angle of incidence exceeds critical angle. [1]",
                "citations": [
                    {
                        "citation_number": 1,
                        "chunk_id": "chk_42",
                        "document_id": "doc_physics_1",
                        "file_name": "ch10_light.pdf",
                        "page_number": 12,
                        "text_snippet": "When light travels from denser to rarer medium...",
                        "collection_id": "subject_physics",
                        "owner_subject_id": "user_teach_1",
                    }
                ],
                "retrieved_chunk_count": 1,
                "duration_ms": 42.5,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    res = await client.generate_answer(
        query="Explain total internal reflection",
        tenant_id="school_sch_1",
        collection_id="subject_physics",
        owner_subject_id="user_teach_1",
        limit=3,
        document_type="TEXTBOOK",
        system_prompt="Be concise",
    )

    assert "Total internal reflection" in res["answer"]
    assert len(res["citations"]) == 1
    assert res["citations"][0]["citation_number"] == 1
    assert res["citations"][0]["document_id"] == "doc_physics_1"

    # Verify headers
    headers = captured_headers[0]
    assert headers["authorization"] == "Bearer ss_live_secret_key"
    assert headers["x-client-id"] == "exam_arena"
    assert headers["x-tenant-id"] == "school_sch_1"
    assert headers["x-collection-id"] == "subject_physics"
    assert headers["x-subject-id"] == "user_teach_1"

    # Verify payload
    payload = captured_payloads[0]
    assert payload["query"] == "Explain total internal reflection"
    assert payload["collection_id"] == "subject_physics"
    assert payload["limit"] == 3
    assert payload["document_type"] == "TEXTBOOK"
    assert payload["system_prompt"] == "Be concise"


@pytest.mark.asyncio
async def test_client_generate_answer_timeout(monkeypatch):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout reading stream")

    transport = httpx.MockTransport(mock_handler)
    mock_async_client(monkeypatch, transport)

    client = SearchSphereClient(
        base_url="http://mock-ss:8000",
        api_key="ss_live_secret_key",
    )

    with pytest.raises(SearchSphereTimeoutError) as exc_info:
        await client.generate_answer(
            query="Explain gravity",
            tenant_id="school_sch_1",
            collection_id="subject_physics",
        )
    assert "Timed out while generating grounded answer" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_generate_answer_error_mappings(monkeypatch):
    status_to_test = [
        (401, SearchSphereAuthenticationError),
        (403, SearchSphereAuthorizationError),
        (404, SearchSphereNotFoundError),
        (500, SearchSphereUnavailableError),
        (503, SearchSphereUnavailableError),
    ]

    for status_code, expected_exc in status_to_test:
        def mock_handler(request: httpx.Request, sc=status_code) -> httpx.Response:
            return httpx.Response(sc, json={"detail": f"Upstream error {sc}"})

        transport = httpx.MockTransport(mock_handler)
        mock_async_client(monkeypatch, transport)

        client = SearchSphereClient(
            base_url="http://mock-ss:8000",
            api_key="ss_live_secret_key",
        )

        with pytest.raises(expected_exc):
            await client.generate_answer(
                query="Query",
                tenant_id="school_sch_1",
                collection_id="subject_physics",
            )

