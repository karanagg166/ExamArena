"""Real PostgreSQL caller revocation while synthetic upstream work is in flight."""

import httpx
import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.models import Role, Student, Teacher, User
from tests.api import test_course_materials_api as material_support
from tests.factories.class_factory import create_class_factory

setup_schools = material_support.setup_schools
mock_search_sphere_key = material_support.mock_search_sphere_key
_async_client = httpx.AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,change",
    [
        (endpoint, change)
        for endpoint in ("search", "answer")
        for change in ("teacher_school", "student_class", "role")
    ]
    + [("cleanup", change) for change in ("teacher_school", "role")],
)
async def test_changed_caller_grant_withholds_upstream_evidence(
    auth_client_factory, setup_schools, db_session, monkeypatch, endpoint, change
):
    schools = setup_schools
    student = change == "student_class"
    class_id = schools["class_a"].id if student else None
    await material_support.seed_material(
        db_session, schools, "synthetic-doc", class_id=class_id
    )
    other_class = await create_class_factory(
        db_session, school=schools["school_a"], section="ZZ", name="Other class"
    )
    await db_session.commit()
    changed_sessions = async_sessionmaker(db_session.bind, expire_on_commit=False)
    captured = []

    async def provider(request):
        captured.append(request)
        async with changed_sessions() as changed, changed.begin():
            if change == "teacher_school":
                await changed.execute(
                    update(Teacher)
                    .where(Teacher.id == schools["teacher_a"].id)
                    .values(schoolId=schools["school_b"].id)
                )
            elif change == "student_class":
                await changed.execute(
                    update(Student)
                    .where(Student.id == schools["student_a"].id)
                    .values(classId=other_class.id)
                )
            else:
                await changed.execute(
                    update(User)
                    .where(User.id == schools["teacher_a_user"].id)
                    .values(role=Role.STUDENT)
                )
        if endpoint == "cleanup":
            return httpx.Response(
                200,
                json={
                    "document_id": "synthetic-doc",
                    "status": "complete",
                    "vectors_remaining": 0,
                    "derived_objects_remaining": 0,
                    "object_deleted": True,
                },
            )
        if endpoint == "search":
            return httpx.Response(
                200,
                json={
                    "query": "synthetic",
                    "total": 1,
                    "duration_ms": 1,
                    "results": [
                        {
                            "document_id": "synthetic-doc",
                            "chunk_id": "synthetic-chunk",
                            "text": "PRIVATE SYNTHETIC EVIDENCE",
                            "score": 0.9,
                            "rank": 1,
                        }
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "answer": "PRIVATE SYNTHETIC EVIDENCE [1]",
                "retrieved_chunk_count": 1,
                "duration_ms": 1,
                "citations": [
                    {
                        "document_id": "synthetic-doc",
                        "chunk_id": "synthetic-chunk",
                        "citation_number": 1,
                        "text_snippet": "PRIVATE SYNTHETIC EVIDENCE",
                        "page_number": 1,
                    }
                ],
            },
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: _async_client(transport=httpx.MockTransport(provider), **kw),
    )
    client = await auth_client_factory(
        schools["student_a_user" if student else "teacher_a_user"]
    )
    payload = {"query": "Public synthetic fixture", "subject": "SCIENCE"}
    if student:
        payload["class_id"] = class_id
    response = (
        await client.get("/api/v1/course-materials/synthetic-doc/cleanup")
        if endpoint == "cleanup"
        else await client.post("/api/v1/course-materials/" + endpoint, json=payload)
    )
    assert len(captured) == 1
    assert response.status_code == 403
    assert "PRIVATE SYNTHETIC EVIDENCE" not in response.text
    assert not any(
        name in response.json() for name in ("answer", "citations", "results")
    )
