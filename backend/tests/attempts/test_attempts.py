# backend/tests/attempts/test_attempts.py

import pytest

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
        assert data["marksObtained"] is None
        assert data["answers"] == []

    async def test_start_invalid(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        mock_attempts_db["start_exam_attempt"].side_effect = ValueError(
            "Exam not found"
        )

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

    async def test_get_attempt_rejects_different_student(
        self, client, override_auth, mock_attempts_db
    ):
        override_auth(role="STUDENT")
        mock_attempts_db["get_attempt_by_id"].return_value = make_fake_student_exam(
            {"studentId": "another_student"}
        )

        response = await client.get("/api/v1/attempts/clxfake_se_001")

        assert response.status_code == 404

    async def test_get_attempt_rejects_staff(
        self, client, override_auth, mock_attempts_db
    ):
        override_auth(role="TEACHER")

        response = await client.get("/api/v1/attempts/clxfake_se_001")

        assert response.status_code == 403

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
                    "selectedOptions": [],
                }
            ],
        }
        response = await client.post("/api/v1/attempts/submit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUBMITTED"

    async def test_submit_late_rejected(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        mock_attempts_db["submit_exam_attempt"].side_effect = ValueError(
            "Exam submission time exceeded. The deadline for this exam has passed."
        )

        payload = {"id": "clxfake_se_001", "answers": []}
        response = await client.post("/api/v1/attempts/submit", json=payload)
        assert response.status_code == 400
        assert "Exam submission time exceeded" in response.json()["detail"]

    async def test_submit_already_submitted_rejected(
        self, client, override_auth, mock_attempts_db
    ):
        override_auth(role="STUDENT")
        mock_attempts_db["submit_exam_attempt"].side_effect = ValueError(
            "This exam has already been submitted and attempted."
        )

        payload = {"id": "clxfake_se_001", "answers": []}
        response = await client.post("/api/v1/attempts/submit", json=payload)
        assert response.status_code == 400
        assert "already been submitted and attempted" in response.json()["detail"]

    async def test_submit_rejects_duplicate_answer_ids(
        self, client, override_auth, mock_attempts_db
    ):
        override_auth(role="STUDENT")
        payload = {
            "id": "clxfake_se_001",
            "answers": [
                {"id": "ans_001", "selectedOptions": []},
                {"id": "ans_001", "selectedOptions": []},
            ],
        }

        response = await client.post("/api/v1/attempts/submit", json=payload)

        assert response.status_code == 422
        mock_attempts_db["submit_exam_attempt"].assert_not_awaited()

    async def test_save_draft_success(self, client, override_auth, mock_attempts_db):
        override_auth(role="STUDENT")
        from datetime import UTC, datetime

        from app.attempts.schemas import StudentExamDraftResponse

        fake_resp = StudentExamDraftResponse(
            attemptId="clxfake_se_001",
            savedCount=1,
            clientSequence=1,
            savedAt=datetime.now(UTC),
            timeRemainingSeconds=3500,
        )
        mock_attempts_db["save_attempt_draft"].return_value = fake_resp

        payload = {
            "clientSequence": 1,
            "answers": [
                {
                    "id": "ans_001",
                    "questionId": "q_001",
                    "textAnswer": "Autosaved draft answer",
                    "selectedOptions": [],
                }
            ],
        }
        response = await client.put("/api/v1/attempts/clxfake_se_001/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["attemptId"] == "clxfake_se_001"
        assert data["savedCount"] == 1
        assert data["clientSequence"] == 1

    async def test_save_draft_requires_student(
        self, client, override_auth, mock_attempts_db
    ):
        override_auth(role="TEACHER")
        payload = {"clientSequence": 1, "answers": []}
        response = await client.put("/api/v1/attempts/clxfake_se_001/draft", json=payload)
        assert response.status_code == 403
        mock_attempts_db["save_attempt_draft"].assert_not_awaited()

    async def test_save_draft_expired_or_submitted_rejected(
        self, client, override_auth, mock_attempts_db
    ):
        override_auth(role="STUDENT")
        mock_attempts_db["save_attempt_draft"].side_effect = ValueError(
            "Cannot modify answers for an already submitted attempt"
        )
        payload = {"clientSequence": 1, "answers": []}
        response = await client.put("/api/v1/attempts/clxfake_se_001/draft", json=payload)
        assert response.status_code == 400
        assert "Cannot modify answers" in response.json()["detail"]

