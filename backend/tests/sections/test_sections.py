# backend/tests/sections/test_sections.py
from datetime import datetime
from unittest.mock import MagicMock

import pytest


def make_fake_section(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}
    section = MagicMock()
    section.id = "clxfake_section_001"
    section.name = "Section A"
    section.description = "First section"
    section.questionType = "MULTIPLE_CHOICE"
    section.marksPerQuestion = 5
    section.sortOrder = 1
    section.examId = "clxfake_exam_001"
    section.createdAt = datetime(2026, 1, 1)
    section.updatedAt = datetime(2026, 1, 1)
    for k, v in overrides.items():
        setattr(section, k, v)
    return section


@pytest.mark.asyncio
class TestSectionsApi:
    # ── POST /api/v1/sections ────────────────────────────────
    async def test_create_section_success(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )
        fake_section = make_fake_section()
        mock_sections_db["create_section"].return_value = fake_section

        payload = {
            "name": "Section A",
            "questionType": "MULTIPLE_CHOICE",
            "marksPerQuestion": 5,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_section.id
        assert data["name"] == "Section A"

    async def test_create_section_invalid_name_number(
        self, client, override_auth, mock_sections_db
    ):
        """Section names like 'Section 1' must be rejected."""
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )

        payload = {
            "name": "Section 1",
            "questionType": "MULTIPLE_CHOICE",
            "marksPerQuestion": 5,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 422

    async def test_create_section_invalid_name_lowercase(
        self, client, override_auth, mock_sections_db
    ):
        """Section names like 'Section a' must be rejected."""
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )

        payload = {
            "name": "Section a",
            "questionType": "MULTIPLE_CHOICE",
            "marksPerQuestion": 5,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 422

    async def test_create_section_invalid_name_freeform(
        self, client, override_auth, mock_sections_db
    ):
        """Freeform names like 'first section' must be rejected."""
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )

        payload = {
            "name": "first section",
            "questionType": "MULTIPLE_CHOICE",
            "marksPerQuestion": 5,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 422

    async def test_create_section_not_teacher(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="STUDENT")

        payload = {
            "name": "Section A",
            "questionType": "MULTIPLE_CHOICE",
            "marksPerQuestion": 5,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 403
        assert "Only teachers can manage sections" in response.json()["detail"]

    async def test_create_section_invalid_marks_zero(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )

        payload = {
            "name": "Section A",
            "questionType": "MULTIPLE_CHOICE",
            "marksPerQuestion": 0,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 422

    async def test_create_section_valid_name_z(
        self, client, override_auth, mock_sections_db
    ):
        """'Section Z' is a valid section name."""
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )
        fake_section = make_fake_section({"name": "Section Z", "sortOrder": 26})
        mock_sections_db["create_section"].return_value = fake_section

        payload = {
            "name": "Section Z",
            "questionType": "ESSAY",
            "marksPerQuestion": 10,
            "examId": "clxfake_exam_001",
        }
        response = await client.post("/api/v1/sections", json=payload)
        assert response.status_code == 201
        assert response.json()["name"] == "Section Z"

    # ── GET /api/v1/sections/exam/{exam_id} ──────────────────
    async def test_get_exam_sections(self, client, override_auth, mock_sections_db):
        override_auth(role="TEACHER")
        sec_a = make_fake_section()
        sec_b = make_fake_section(
            {"id": "clxfake_section_002", "name": "Section B", "sortOrder": 2}
        )
        mock_sections_db["get_sections_by_exam"].return_value = [sec_a, sec_b]

        response = await client.get("/api/v1/sections/exam/clxfake_exam_001")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Section A"
        assert data[1]["name"] == "Section B"

    # ── GET /api/v1/sections/{section_id} ────────────────────
    async def test_get_section_by_id(self, client, override_auth, mock_sections_db):
        override_auth(role="TEACHER")
        fake_section = make_fake_section()
        mock_sections_db["get_section_by_id"].return_value = fake_section

        response = await client.get(f"/api/v1/sections/{fake_section.id}")
        assert response.status_code == 200
        assert response.json()["id"] == fake_section.id

    async def test_get_section_not_found(self, client, override_auth, mock_sections_db):
        override_auth(role="TEACHER")
        mock_sections_db["get_section_by_id"].return_value = None

        response = await client.get("/api/v1/sections/clxfake_section_999")
        assert response.status_code == 404
        assert "Section not found" in response.json()["detail"]

    # ── PATCH /api/v1/sections/{section_id} ──────────────────
    async def test_patch_section_success(self, client, override_auth, mock_sections_db):
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )
        fake_section = make_fake_section()
        mock_sections_db["get_section_by_id"].return_value = fake_section

        updated = make_fake_section({"description": "Updated description"})
        mock_sections_db["update_section"].return_value = updated

        response = await client.patch(
            f"/api/v1/sections/{fake_section.id}",
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    async def test_patch_section_not_found(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )
        mock_sections_db["get_section_by_id"].return_value = None

        response = await client.patch(
            "/api/v1/sections/clxfake_section_999",
            json={"description": "Updated"},
        )
        assert response.status_code == 404

    async def test_patch_section_not_teacher(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="STUDENT")

        response = await client.patch(
            "/api/v1/sections/clxfake_section_001",
            json={"description": "Updated"},
        )
        assert response.status_code == 403

    # ── DELETE /api/v1/sections/{section_id} ─────────────────
    async def test_delete_section_success(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )
        fake_section = make_fake_section()
        mock_sections_db["get_section_by_id"].return_value = fake_section

        response = await client.delete(f"/api/v1/sections/{fake_section.id}")
        assert response.status_code == 204
        mock_sections_db["delete_section"].assert_called_once_with(fake_section.id)

    async def test_delete_section_not_found(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="TEACHER")
        mock_sections_db["get_teacher_by_user_id"].return_value = MagicMock(
            id="teacher_001"
        )
        mock_sections_db["get_section_by_id"].return_value = None

        response = await client.delete("/api/v1/sections/clxfake_section_999")
        assert response.status_code == 404

    async def test_delete_section_not_teacher(
        self, client, override_auth, mock_sections_db
    ):
        override_auth(role="STUDENT")

        response = await client.delete("/api/v1/sections/clxfake_section_001")
        assert response.status_code == 403
