"""Actual HTTP/PostgreSQL catalog authorization; all material/provider data synthetic."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import HTTPException

from app.core.models import Role
from app.course_materials.permissions import resolve_user_material_scope
from tests.api import test_course_materials_api as material_support
from tests.factories.class_factory import create_class_factory

_async_client = httpx.AsyncClient
setup_schools = material_support.setup_schools
mock_search_sphere_key = material_support.mock_search_sphere_key
seed_material = material_support.seed_material


@pytest.fixture
async def catalog(db_session, setup_schools):
    schools = setup_schools
    other = await create_class_factory(
        db_session,
        school=schools["school_a"],
        name="Other enrolled class",
        section="ZZ",
    )
    rows = {
        "own": await seed_material(
            db_session, schools, "own-class", class_id=schools["class_a"].id
        ),
        "general": await seed_material(db_session, schools, "school-wide"),
        "other": await seed_material(
            db_session, schools, "other-class", class_id=other.id
        ),
        "foreign": await seed_material(
            db_session,
            schools,
            "other-school",
            school="b",
            class_id=schools["class_b"].id,
        ),
    }
    return schools, rows


@pytest.mark.asyncio
async def test_student_default_catalog_and_pagination_include_only_enrolled_class_and_school_wide(
    auth_client_factory, catalog
):
    schools, rows = catalog
    client = await auth_client_factory(schools["student_a_user"])
    response = await client.get("/api/v1/course-materials")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {row["id"] for row in response.json()["items"]} == {
        rows["own"].id,
        rows["general"].id,
    }
    first = await client.get("/api/v1/course-materials?limit=1&offset=0")
    second = await client.get("/api/v1/course-materials?limit=1&offset=1")
    assert first.json()["total"] == second.json()["total"] == 2
    assert {first.json()["items"][0]["id"], second.json()["items"][0]["id"]} == {
        rows["own"].id,
        rows["general"].id,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "which,status", [("own", 200), ("general", 200), ("other", 404), ("foreign", 404)]
)
async def test_student_individual_catalog_reads_require_class_access(
    auth_client_factory, catalog, which, status
):
    schools, rows = catalog
    client = await auth_client_factory(schools["student_a_user"])
    response = await client.get("/api/v1/course-materials/" + rows[which].id)
    assert response.status_code == status
    if status == 404:
        assert "searchSphereDocumentId" not in response.json()


@pytest.mark.asyncio
async def test_principal_retains_school_catalog_access(auth_client_factory, catalog):
    schools, rows = catalog
    client = await auth_client_factory(schools["principal_a_user"])
    response = await client.get("/api/v1/course-materials")
    assert response.status_code == 200 and response.json()["total"] == 3
    assert {row["id"] for row in response.json()["items"]} == {
        rows[key].id for key in ("own", "general", "other")
    }


@pytest.mark.asyncio
async def test_upload_rejects_another_schools_class_before_any_upstream_call(
    auth_client_factory, setup_schools, monkeypatch
):
    captured = []

    def provider(request):
        captured.append(request)
        if request.url.path == "/api/v1/collections":
            return httpx.Response(201, json={"collection_id": "synthetic"})
        if request.url.path.endswith("/upload"):
            return httpx.Response(
                201,
                json={
                    "storage_key": "synthetic.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 100,
                },
            )
        return httpx.Response(202, json={"id": "synthetic", "status": "PROCESSING"})

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: _async_client(
            transport=httpx.MockTransport(provider), **kwargs
        ),
    )
    client = await auth_client_factory(setup_schools["teacher_a_user"])
    response = await client.post(
        "/api/v1/course-materials/upload",
        data={
            "title": "Synthetic class authorization",
            "subject": "SCIENCE",
            "class_id": setup_schools["class_b"].id,
        },
        files={
            "file": ("public.pdf", b"%PDF-1.4 synthetic fixture", "application/pdf")
        },
    )
    assert response.status_code == 404
    assert captured == []


@pytest.mark.asyncio
@pytest.mark.parametrize("class_id", [None, ""])
async def test_missing_student_enrollment_never_becomes_unrestricted_staff_scope(
    class_id,
):
    row = SimpleNamespace(schoolId="synthetic-school", classId=class_id)
    result = Mock()
    result.scalar_one_or_none.return_value = row
    session = SimpleNamespace(
        execute=AsyncMock(return_value=result), scalar=AsyncMock()
    )
    with pytest.raises(HTTPException) as caught:
        await resolve_user_material_scope(
            SimpleNamespace(id="synthetic-user", role=Role.STUDENT), None, session
        )
    assert caught.value.status_code == 403
    session.scalar.assert_not_awaited()
