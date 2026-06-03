# backend/tests/attempts/test_attempts.py
import pytest
from unittest.mock import MagicMock
from tests.dummy_data.exams import make_fake_student_exam

@pytest.mark.asyncio
class TestAttemptsApi:

    async def test_start_success(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        fake_attempt = make_fake_student_exam()
        mock_attempts_db["start_exam_attempt"].return_value = fake_attempt

        response = await client.post(
            "/api/v1/attempts/start",
            json={"examId": "clxfake_exam_001"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_attempt.id
        assert data["status"] == "IN_PROGRESS"
        assert data["marksObtained"] == 0
        assert data["answers"] == []

    async def test_start_invalid(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        mock_attempts_db["start_exam_attempt"].side_effect = ValueError("Exam not found")

        response = await client.post(
            "/api/v1/attempts/start",
            json={"examId": "clxfake_exam_001"},
        )
        assert response.status_code == 400
        assert "Exam not found" in response.json()["detail"]

    async def test_get_attempt_success(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        fake_attempt = make_fake_student_exam()
        mock_attempts_db["get_attempt_by_id"].return_value = fake_attempt

        response = await client.get(f"/api/v1/attempts/{fake_attempt.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_attempt.id

    async def test_get_attempt_not_found(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        mock_attempts_db["get_attempt_by_id"].return_value = None

        response = await client.get("/api/v1/attempts/clxfake_se_999")
        assert response.status_code == 404
        assert "Attempt not found" in response.json()["detail"]

    async def test_submit_success(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        fake_attempt = make_fake_student_exam({"status": "SUBMITTED"})
        mock_attempts_db["submit_exam_attempt"].return_value = fake_attempt

        payload = {
            "id": "clxfake_se_001",
            "answers": [
                {
                    "id": "ans_001",
                    "textAnswer": "Some written text",
                    "selectedOptions": []
                }
            ]
        }
        response = await client.post("/api/v1/attempts/submit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUBMITTED"

    async def test_submit_invalid(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        mock_attempts_db["submit_exam_attempt"].side_effect = ValueError("Attempt already submitted")

        payload = {
            "id": "clxfake_se_001",
            "answers": []
        }
        response = await client.post("/api/v1/attempts/submit", json=payload)
        assert response.status_code == 400
        assert "Attempt already submitted" in response.json()["detail"]
