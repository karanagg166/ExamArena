"""Assigned-class authorization before and after delegated upstream operations."""

from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import delete, update

from app.core.models import CourseMaterial, SchoolClass, TeacherClass
from app.course_materials.router import get_course_material_service
from app.main import app
from tests.api import test_course_material_catalog_scope as support

catalog = support.catalog
setup_schools = support.setup_schools
mock_search_sphere_key = support.mock_search_sphere_key


@pytest.mark.asyncio
async def test_teacher_catalog_and_pagination_only_include_assigned_and_shared(
    auth_client_factory, catalog
):
    schools, rows = catalog
    client = await auth_client_factory(schools["teacher_a_user"])
    found = set()
    for offset in (0, 1):
        response = await client.get(f"/api/v1/course-materials?limit=1&offset={offset}")
        assert response.status_code == 200
        assert response.json()["total"] == 2
        found.add(response.json()["items"][0]["id"])
    assert found == {rows["own"].id, rows["general"].id}
    assert (
        await client.get("/api/v1/course-materials/" + rows["other"].id)
    ).status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation", ["upload", "refresh-status", "delete", "search", "answer", "cleanup"]
)
async def test_unassigned_class_cannot_reach_upstream(
    auth_client_factory, catalog, monkeypatch, operation
):
    schools, rows = catalog
    client = await auth_client_factory(schools["teacher_a_user"])
    calls = []
    original = httpx.AsyncClient

    def handle(request):
        calls.append(request)
        return httpx.Response(500)

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs),
    )
    class_id = rows["other"].classId
    if operation == "upload":
        response = await client.post(
            "/api/v1/course-materials/upload",
            data={"title": "Synthetic", "subject": "SCIENCE", "class_id": class_id},
            files={"file": ("public.pdf", b"%PDF-1.4 synthetic", "application/pdf")},
        )
    elif operation in ("search", "answer"):
        response = await client.post(
            "/api/v1/course-materials/" + operation,
            json={
                "query": "Synthetic question",
                "subject": "SCIENCE",
                "class_id": class_id,
            },
        )
    elif operation == "delete":
        response = await client.delete("/api/v1/course-materials/" + rows["other"].id)
    elif operation == "cleanup":
        response = await client.get(
            f'/api/v1/course-materials/{rows["other"].id}/cleanup?subject=SCIENCE&class_id={class_id}'
        )
    else:
        response = await client.post(
            f'/api/v1/course-materials/{rows["other"].id}/refresh-status'
        )
    assert response.status_code in (403, 404)
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["search", "answer"])
async def test_assignment_revoked_during_upstream_work_denies_result(
    auth_client_factory, catalog, db_session, route
):
    schools, _ = catalog
    client = await auth_client_factory(schools["teacher_a_user"])

    async def revoke(**kwargs):
        await db_session.execute(
            delete(TeacherClass).where(
                TeacherClass.teacherId == schools["teacher_a"].id
            )
        )
        await db_session.commit()
        return {
            "answer": "Synthetic private answer",
            "citations": [],
            "results": [],
            "total": 0,
        }

    service = AsyncMock()
    service.search_materials.side_effect = revoke
    service.answer_question.side_effect = revoke
    app.dependency_overrides[get_course_material_service] = lambda: service
    try:
        response = await client.post(
            "/api/v1/course-materials/" + route,
            json={
                "query": "Synthetic question",
                "subject": "SCIENCE",
                "class_id": schools["class_a"].id,
            },
        )
    finally:
        app.dependency_overrides.pop(get_course_material_service, None)
    assert response.status_code == 403
    assert "Synthetic private answer" not in response.text


@pytest.mark.asyncio
async def test_teacher_without_assignments_only_sees_shared_materials(
    auth_client_factory, catalog, db_session
):
    schools, rows = catalog
    await db_session.execute(
        delete(TeacherClass).where(TeacherClass.teacherId == schools["teacher_a"].id)
    )
    await db_session.commit()
    client = await auth_client_factory(schools["teacher_a_user"])
    response = await client.get("/api/v1/course-materials")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert [row["id"] for row in response.json()["items"]] == [rows["general"].id]


@pytest.mark.asyncio
async def test_class_deletion_never_promotes_a_document_to_shared(
    auth_client_factory, catalog, db_session
):
    schools, rows = catalog
    # The database's legacy ON DELETE SET NULL must not change evidence scope.
    await db_session.execute(
        delete(SchoolClass).where(SchoolClass.id == rows["other"].classId)
    )
    await db_session.commit()
    for actor in ("teacher_a_user", "student_a_user"):
        client = await auth_client_factory(schools[actor])
        response = await client.get("/api/v1/course-materials")
        assert rows["other"].id not in {row["id"] for row in response.json()["items"]}
        assert (
            await client.get("/api/v1/course-materials/" + rows["other"].id)
        ).status_code == 404


@pytest.mark.asyncio
async def test_cleanup_without_scope_does_not_use_school_wide_credential(
    auth_client_factory, setup_schools, monkeypatch
):
    client = await auth_client_factory(setup_schools["teacher_a_user"])
    handler = AsyncMock()
    monkeypatch.setattr(
        "app.integrations.search_sphere.client.SearchSphereClient.get_document_cleanup",
        handler,
    )
    response = await client.get("/api/v1/course-materials/synthetic/cleanup")
    assert response.status_code == 422
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_cleanup_is_bound_to_deleted_documents_collection(
    auth_client_factory, setup_schools, monkeypatch
):
    from app.integrations.search_sphere.identifiers import build_collection_id

    schools = setup_schools
    class_id = schools["class_a"].id
    collection = build_collection_id("SCIENCE", class_id)
    original = httpx.AsyncClient
    calls = []

    def upstream(request):
        calls.append(request)
        # Search Sphere checks its durable tombstone against X-Collection-ID.
        if request.headers["x-collection-id"] != collection:
            return httpx.Response(403, json={"detail": "Scope conflict"})
        return httpx.Response(
            200,
            json={
                "document_id": "synthetic-deleted",
                "status": "complete",
                "vectors_remaining": 0,
                "derived_objects_remaining": 0,
                "object_deleted": True,
            },
        )

    client = await auth_client_factory(schools["teacher_a_user"])
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(upstream), **kw),
    )
    path = "/api/v1/course-materials/synthetic-deleted/cleanup?subject=SCIENCE"
    assert (await client.get(path)).status_code == 404
    response = await client.get(path + "&class_id=" + class_id)
    assert response.status_code == 200
    assert calls[-1].headers["x-collection-id"] == collection
    assert calls[-1].headers["x-tenant-id"] == "school_" + schools["school_a"].id
