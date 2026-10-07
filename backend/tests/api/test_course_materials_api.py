"""API and Tenant Isolation Tests for Course Materials.

Critical verifications:
1. Multi-tenant isolation: School A vs School B (distinct tenants, identical filenames/doc IDs).
2. Collection isolation: Subject and class material boundaries.
3. Service credential security: SEARCH_SPHERE_API_KEY never leaks.
4. Role permissions and student search boundary enforcement.
5. Ingestion, status refresh, and deletion lifecycle.
"""

import io
import json
from pathlib import Path
import pytest
import httpx

from app.core.config import settings
from app.core.models import (
    CourseMaterial,
    CourseMaterialDocumentType,
    CourseMaterialStatus,
    Role,
    Subject,
)
from tests.factories.class_factory import create_class_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory

_orig_async_client = httpx.AsyncClient


@pytest.fixture(autouse=True)
def mock_search_sphere_key(monkeypatch):
    monkeypatch.setattr(settings, "SEARCH_SPHERE_API_KEY", "ss_live_test_api_key_12345")


@pytest.fixture
async def setup_schools(db_session):
    """Sets up two isolated schools with teachers and students."""
    # School A
    user_p_a = await create_user_factory(db_session, role=Role.PRINCIPAL, email="principal_a@school.local")
    school_a = await create_school_factory(db_session, creator_user=user_p_a, school_code="SCH-A-101")
    user_t_a = await create_user_factory(db_session, role=Role.TEACHER, email="teacher_a@school.local")
    teacher_a = await create_teacher_factory(db_session, user=user_t_a, school=school_a)
    class_a = await create_class_factory(db_session, school=school_a, name="Class 10A")
    user_s_a = await create_user_factory(db_session, role=Role.STUDENT, email="student_a@school.local")
    student_a = await create_student_factory(db_session, user=user_s_a, school=school_a, school_class=class_a)

    # School B
    user_p_b = await create_user_factory(db_session, role=Role.PRINCIPAL, email="principal_b@school.local")
    school_b = await create_school_factory(db_session, creator_user=user_p_b, school_code="SCH-B-202")
    user_t_b = await create_user_factory(db_session, role=Role.TEACHER, email="teacher_b@school.local")
    teacher_b = await create_teacher_factory(db_session, user=user_t_b, school=school_b)
    class_b = await create_class_factory(db_session, school=school_b, name="Class 10B")
    user_s_b = await create_user_factory(db_session, role=Role.STUDENT, email="student_b@school.local")
    student_b = await create_student_factory(db_session, user=user_s_b, school=school_b, school_class=class_b)

    await db_session.commit()

    return {
        "school_a": school_a,
        "teacher_a_user": user_t_a,
        "teacher_a": teacher_a,
        "student_a_user": user_s_a,
        "student_a": student_a,
        "class_a": class_a,
        "school_b": school_b,
        "teacher_b_user": user_t_b,
        "teacher_b": teacher_b,
        "student_b_user": user_s_b,
        "student_b": student_b,
        "class_b": class_b,
    }


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_course_materials(client):
    res = await client.get("/api/v1/course-materials")
    assert res.status_code == 401

    res = await client.post("/api/v1/course-materials/upload")
    assert res.status_code == 401

    res = await client.post("/api/v1/course-materials/search", json={"query": "test", "subject": "SCIENCE"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_upload_course_materials(auth_client_factory, setup_schools):
    student_client = await auth_client_factory(setup_schools["student_a_user"])

    files = {"file": ("notes.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    data = {"title": "Student Notes", "subject": "SCIENCE"}

    res = await student_client.post("/api/v1/course-materials/upload", data=data, files=files)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_teacher_upload_course_material(auth_client_factory, setup_schools, monkeypatch):
    captured_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        if request.url.path == "/api/v1/collections":
            return httpx.Response(201, json={"collection_id": "subject_science", "name": "SCIENCE Materials"})
        if request.url.path == "/api/v1/documents/upload":
            return httpx.Response(201, json={"storage_key": "storage/path/phy.pdf", "mime_type": "application/pdf", "file_size": 100})
        if request.url.path == "/api/v1/documents":
            return httpx.Response(202, json={"id": "ss_doc_physics_001", "status": "PROCESSING"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])
    school_a = setup_schools["school_a"]

    files = {"file": ("physics_textbook.pdf", b"%PDF-1.4 sample content", "application/pdf")}
    data = {
        "title": "Grade 10 Physics Textbook",
        "subject": "SCIENCE",
        "document_type": "TEXTBOOK",
        "description": "NCERT prescribed syllabus",
    }

    res = await teacher_client.post("/api/v1/course-materials/upload", data=data, files=files)
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "Grade 10 Physics Textbook"
    assert body["searchSphereDocumentId"] == "ss_doc_physics_001"
    assert body["searchSphereCollectionId"] == "subject_science"
    assert body["status"] == "PROCESSING"

    # Verify requests sent to Search-Sphere carried School A tenant
    assert len(captured_requests) >= 3
    for req in captured_requests:
        assert req.headers["x-client-id"] == "exam_arena"
        assert req.headers["x-tenant-id"] == f"school_{school_a.id}"


@pytest.mark.asyncio
async def test_tenant_isolation_school_a_vs_school_b(auth_client_factory, setup_schools, monkeypatch):
    captured_tenants: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_tenants.append(request.headers.get("x-tenant-id", ""))
        if request.url.path == "/api/v1/collections":
            return httpx.Response(201, json={"collection_id": "subject_maths", "name": "MATHS Materials"})
        if request.url.path == "/api/v1/documents/upload":
            return httpx.Response(201, json={"storage_key": "storage/path/m.pdf", "mime_type": "application/pdf", "file_size": 50})
        if request.url.path == "/api/v1/documents":
            return httpx.Response(202, json={"id": f"doc_{len(captured_tenants)}", "status": "PROCESSING"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_a_client = await auth_client_factory(setup_schools["teacher_a_user"])
    teacher_b_client = await auth_client_factory(setup_schools["teacher_b_user"])

    school_a = setup_schools["school_a"]
    school_b = setup_schools["school_b"]

    files = {"file": ("common_syllabus.pdf", b"%PDF-1.4 common syllabus bytes", "application/pdf")}
    data = {"title": "Common Syllabus", "subject": "MATHS", "document_type": "SYLLABUS"}

    # 1. School A upload
    res_a = await teacher_a_client.post("/api/v1/course-materials/upload", data=data, files=files)
    assert res_a.status_code == 201
    mat_a_id = res_a.json()["id"]

    # 2. School B upload
    files_b = {"file": ("common_syllabus.pdf", b"%PDF-1.4 common syllabus bytes", "application/pdf")}
    res_b = await teacher_b_client.post("/api/v1/course-materials/upload", data=data, files=files_b)
    assert res_b.status_code == 201
    mat_b_id = res_b.json()["id"]

    # Verify that School A requests only used school_a tenant, and School B only school_b
    assert f"school_{school_a.id}" in captured_tenants
    assert f"school_{school_b.id}" in captured_tenants
    assert captured_tenants[0] == f"school_{school_a.id}"
    assert captured_tenants[-1] == f"school_{school_b.id}"

    # 3. Cross-Tenant Denial: Teacher A cannot fetch or delete School B's material
    res_cross_get = await teacher_a_client.get(f"/api/v1/course-materials/{mat_b_id}")
    assert res_cross_get.status_code == 404

    res_cross_del = await teacher_a_client.delete(f"/api/v1/course-materials/{mat_b_id}")
    assert res_cross_del.status_code == 404


@pytest.mark.asyncio
async def test_collection_isolation_maths_vs_science(auth_client_factory, setup_schools, monkeypatch):
    captured_payloads: list[dict] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        captured_payloads.append(payload)
        return httpx.Response(
            200,
            json={
                "query": payload["query"],
                "total": 0,
                "results": [],
                "duration_ms": 10.0,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])

    # Search Maths
    await teacher_client.post(
        "/api/v1/course-materials/search",
        json={"query": "Quadratic formula", "subject": "MATHS"},
    )
    assert captured_payloads[0]["collection_id"] == "subject_maths"

    # Search Science
    await teacher_client.post(
        "/api/v1/course-materials/search",
        json={"query": "Newton laws", "subject": "SCIENCE"},
    )
    assert captured_payloads[1]["collection_id"] == "subject_science"

    # Search Class-scoped Maths
    class_id = setup_schools["class_a"].id
    await teacher_client.post(
        "/api/v1/course-materials/search",
        json={"query": "Derivatives", "subject": "MATHS", "class_id": class_id},
    )
    assert captured_payloads[2]["collection_id"] == f"class_{class_id}_subject_maths"


@pytest.mark.asyncio
async def test_service_credential_security_no_leakage(auth_client_factory, setup_schools, monkeypatch):
    """
    Guarantees that SEARCH_SPHERE_API_KEY never leaks into API responses,
    error messages, or frontend client configuration.
    """
    secret_key = "ss_live_SUPER_SECRET_TOKEN_DO_NOT_LEAK_XYZ_9999"
    monkeypatch.setattr(settings, "SEARCH_SPHERE_API_KEY", secret_key)

    # 1. Simulate 502 error from Search-Sphere
    def mock_error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": f"Internal database error with key {secret_key}"})

    transport = httpx.MockTransport(mock_error_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])
    res = await teacher_client.post(
        "/api/v1/course-materials/search",
        json={"query": "Chemical reactions", "subject": "SCIENCE"},
    )
    assert res.status_code == 502
    assert secret_key not in res.text
    assert secret_key not in str(res.headers)

    # 2. Inspect frontend directory for forbidden NEXT_PUBLIC_SEARCH_SPHERE_API_KEY
    frontend_dir = Path("/Users/karanagg/Desktop/Projects/exam-arena/src")
    if frontend_dir.exists():
        for file_path in frontend_dir.rglob("*.ts*"):
            content = file_path.read_text(encoding="utf-8")
            assert "SEARCH_SPHERE_API_KEY" not in content, f"Found Search-Sphere key reference in frontend: {file_path}"
            assert "NEXT_PUBLIC_SEARCH_SPHERE" not in content, f"Found NEXT_PUBLIC_SEARCH_SPHERE in frontend: {file_path}"


@pytest.mark.asyncio
async def test_student_search_authorization(auth_client_factory, setup_schools, monkeypatch):
    captured_tenants: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_tenants.append(request.headers.get("x-tenant-id", ""))
        return httpx.Response(200, json={"query": "gravity", "total": 0, "results": [], "duration_ms": 5.0})

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    student_a_client = await auth_client_factory(setup_schools["student_a_user"])
    school_a = setup_schools["school_a"]
    class_a = setup_schools["class_a"]
    class_b = setup_schools["class_b"]

    # 1. Student searches within their enrolled school & class -> OK
    res = await student_a_client.post(
        "/api/v1/course-materials/search",
        json={"query": "gravity", "subject": "SCIENCE", "class_id": class_a.id},
    )
    assert res.status_code == 200
    assert captured_tenants[-1] == f"school_{school_a.id}"

    # 2. Student attempts to search another class -> 403 Forbidden
    res_foreign_class = await student_a_client.post(
        "/api/v1/course-materials/search",
        json={"query": "gravity", "subject": "SCIENCE", "class_id": class_b.id},
    )
    assert res_foreign_class.status_code == 403


@pytest.mark.asyncio
async def test_refresh_and_delete_endpoints(auth_client_factory, setup_schools, monkeypatch):
    calls: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path == "/api/v1/collections":
            return httpx.Response(201, json={"collection_id": "subject_history", "name": "HISTORY"})
        if request.url.path == "/api/v1/documents/upload":
            return httpx.Response(201, json={"storage_key": "storage/path/h.pdf", "mime_type": "application/pdf", "file_size": 50})
        if request.url.path == "/api/v1/documents":
            return httpx.Response(202, json={"id": "ss_doc_hist_1", "status": "PROCESSING"})
        if request.url.path == "/api/v1/documents/ss_doc_hist_1":
            if request.method == "GET":
                return httpx.Response(200, json={"id": "ss_doc_hist_1", "status": "READY"})
            if request.method == "DELETE":
                return httpx.Response(200, json={"success": True})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])

    # 1. Upload
    files = {"file": ("world_war.pdf", b"%PDF-1.4 history", "application/pdf")}
    data = {"title": "World War II Notes", "subject": "HISTORY"}
    res_up = await teacher_client.post("/api/v1/course-materials/upload", data=data, files=files)
    assert res_up.status_code == 201
    mat_id = res_up.json()["id"]

    # 2. Refresh Status
    res_ref = await teacher_client.post(f"/api/v1/course-materials/{mat_id}/refresh-status")
    assert res_ref.status_code == 200
    assert res_ref.json()["status"] == "READY"

    # 3. Delete
    res_del = await teacher_client.delete(f"/api/v1/course-materials/{mat_id}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # 4. Verify no longer exists
    res_get = await teacher_client.get(f"/api/v1/course-materials/{mat_id}")
    assert res_get.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_cannot_ask_answer(client):
    res = await client.post(
        "/api/v1/course-materials/answer",
        json={"query": "Explain Ohm's law", "subject": "SCIENCE"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_teacher_answer_question_valid_request(auth_client_factory, setup_schools, monkeypatch):
    captured_headers: list[httpx.Headers] = []
    captured_payloads: list[dict] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(request.headers)
        payload = json.loads(request.content.decode("utf-8"))
        captured_payloads.append(payload)
        return httpx.Response(
            200,
            json={
                "answer": "Ohm's law states that current is directly proportional to voltage. [1]",
                "citations": [
                    {
                        "citation_number": 1,
                        "chunk_id": "chk_ohm_1",
                        "document_id": "doc_ohm",
                        "file_name": "ohms_law.pdf",
                        "page_number": 5,
                        "text_snippet": "V = IR where R is resistance...",
                        "collection_id": "subject_science",
                        "owner_subject_id": "user_teach_1",
                    }
                ],
                "retrieved_chunk_count": 1,
                "duration_ms": 32.1,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])
    school_a = setup_schools["school_a"]

    res = await teacher_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "Explain Ohm's law", "subject": "SCIENCE"},
    )

    assert res.status_code == 200
    data = res.json()
    assert "Ohm's law states" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["citationNumber"] == 1
    assert data["citations"][0]["fileName"] == "ohms_law.pdf"
    assert data["citations"][0]["pageNumber"] == 5
    assert data["citations"][0]["textSnippet"] == "V = IR where R is resistance..."
    assert data["retrievedChunkCount"] == 1

    # Verify tenant isolation and collection derivation
    assert captured_headers[0]["x-tenant-id"] == f"school_{school_a.id}"
    assert captured_payloads[0]["collection_id"] == "subject_science"
    assert captured_payloads[0]["query"] == "Explain Ohm's law"


@pytest.mark.asyncio
async def test_student_answer_question_authorization(auth_client_factory, setup_schools, monkeypatch):
    captured_headers: list[httpx.Headers] = []
    captured_payloads: list[dict] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(request.headers)
        captured_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "answer": "Photosynthesis produces glucose from sunlight. [1]",
                "citations": [
                    {
                        "citation_number": 1,
                        "chunk_id": "chk_photo",
                        "document_id": "doc_photo",
                        "file_name": "bio.pdf",
                        "page_number": 12,
                        "text_snippet": "Plants make food...",
                    }
                ],
                "retrieved_chunk_count": 1,
                "duration_ms": 15.0,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    student_a_client = await auth_client_factory(setup_schools["student_a_user"])
    school_a = setup_schools["school_a"]
    class_a = setup_schools["class_a"]
    class_b = setup_schools["class_b"]

    # 1. Student in class_a queries class_a -> 200 OK
    res = await student_a_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "What is photosynthesis?", "subject": "SCIENCE", "class_id": class_a.id},
    )
    assert res.status_code == 200
    assert captured_headers[-1]["x-tenant-id"] == f"school_{school_a.id}"
    assert captured_payloads[-1]["collection_id"] == f"class_{class_a.id}_subject_science"

    # 2. Student queries class_b (different class) -> 403 Forbidden
    res_forbidden = await student_a_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "What is photosynthesis?", "subject": "SCIENCE", "class_id": class_b.id},
    )
    assert res_forbidden.status_code == 403


@pytest.mark.asyncio
async def test_cross_school_answer_isolation(auth_client_factory, setup_schools, monkeypatch):
    captured_tenants: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_tenants.append(request.headers.get("x-tenant-id", ""))
        return httpx.Response(200, json={"answer": "Safe answer", "citations": [], "duration_ms": 10.0})

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_b_client = await auth_client_factory(setup_schools["teacher_b_user"])
    school_b = setup_schools["school_b"]

    res = await teacher_b_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "Explain chemistry", "subject": "SCIENCE"},
    )
    assert res.status_code == 200
    assert captured_tenants[-1] == f"school_{school_b.id}"


@pytest.mark.asyncio
async def test_answer_no_evidence_preserved(auth_client_factory, setup_schools, monkeypatch):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "answer": "I couldn't find relevant information in your documents to answer that question.",
                "citations": [],
                "retrieved_chunk_count": 0,
                "duration_ms": 8.5,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])
    res = await teacher_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "Irrelevant query about Mars exploration", "subject": "SCIENCE"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "couldn't find" in data["answer"].lower()
    assert data["citations"] == []
    assert data["retrievedChunkCount"] == 0


@pytest.mark.asyncio
async def test_answer_upstream_error_and_timeout(auth_client_factory, setup_schools, monkeypatch):
    # 1. 500 upstream
    def mock_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "Upstream Cohere service crashed"})

    transport_500 = httpx.MockTransport(mock_500)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport_500, **kwargs))

    teacher_client = await auth_client_factory(setup_schools["teacher_a_user"])
    res_500 = await teacher_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "Explain gravity", "subject": "SCIENCE"},
    )
    assert res_500.status_code == 502
    assert "Grounded answer generation service error" in res_500.json()["detail"]

    # 2. Timeout upstream
    def mock_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout reading stream")

    transport_timeout = httpx.MockTransport(mock_timeout)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _orig_async_client(transport=transport_timeout, **kwargs))

    res_timeout = await teacher_client.post(
        "/api/v1/course-materials/answer",
        json={"query": "Explain gravity", "subject": "SCIENCE"},
    )
    assert res_timeout.status_code == 502
    assert "Timed out while generating grounded answer" in res_timeout.json()["detail"]

