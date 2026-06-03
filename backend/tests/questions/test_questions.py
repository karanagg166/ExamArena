# backend/tests/questions/test_questions.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime

def make_fake_question(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}
    q = MagicMock()
    q.id = "clxfake_q_001"
    q.text = "What is 2 + 2?"
    q.marks = 5
    q.questionNumber = 1
    q.questionType = "MULTIPLE_CHOICE"
    q.imageUrl = None
    q.wordLimit = None
    q.explanation = "2 + 2 = 4"
    q.examId = "clxfake_exam_001"
    q.section = "General"
    q.createdAt = datetime(2026, 1, 1)
    q.updatedAt = datetime(2026, 1, 1)
    q.options = []
    
    for k, v in overrides.items():
        setattr(q, k, v)
    return q

@pytest.mark.asyncio
class TestQuestionsApi:

    async def test_add_question_success(self, client, override_auth, mock_questions_db):
        override_auth(role="TEACHER")
        mock_questions_db["get_teacher_by_user_id"].return_value = MagicMock(id="teacher_001")
        fake_question = make_fake_question()
        mock_questions_db["create_question"].return_value = fake_question

        payload = {
            "text": "What is 2 + 2?",
            "marks": 5,
            "questionNumber": 1,
            "questionType": "MULTIPLE_CHOICE",
            "examId": "clxfake_exam_001",
            "section": "General",
            "options": []
        }
        response = await client.post("/api/v1/questions", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_question.id
        assert data["text"] == fake_question.text

    async def test_add_question_not_teacher(self, client, override_auth, mock_questions_db):
        override_auth(role="STUDENT")

        payload = {
            "text": "What is 2 + 2?",
            "marks": 5,
            "questionNumber": 1,
            "questionType": "MULTIPLE_CHOICE",
            "examId": "clxfake_exam_001",
            "section": "General",
            "options": []
        }
        response = await client.post("/api/v1/questions", json=payload)
        assert response.status_code == 403
        assert "Only teachers can manage questions" in response.json()["detail"]

    async def test_add_question_missing_exam_id(self, client, override_auth, mock_questions_db):
        override_auth(role="TEACHER")
        mock_questions_db["get_teacher_by_user_id"].return_value = MagicMock(id="teacher_001")

        payload = {
            "text": "What is 2 + 2?",
            "marks": 5,
            "questionNumber": 1,
            "questionType": "MULTIPLE_CHOICE",
            "examId": None,
            "section": "General",
            "options": []
        }
        response = await client.post("/api/v1/questions", json=payload)
        assert response.status_code == 400
        assert "examId is required" in response.json()["detail"]

    async def test_patch_success(self, client, override_auth, mock_questions_db):
        override_auth(role="TEACHER")
        mock_questions_db["get_teacher_by_user_id"].return_value = MagicMock(id="teacher_001")
        fake_question = make_fake_question()
        mock_questions_db["get_question_by_id"].return_value = fake_question
        
        updated_question = make_fake_question({"text": "Updated text"})
        mock_questions_db["update_question"].return_value = updated_question

        response = await client.patch(
            f"/api/v1/questions/{fake_question.id}",
            json={"text": "Updated text"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Updated text"

    async def test_patch_not_found(self, client, override_auth, mock_questions_db):
        override_auth(role="TEACHER")
        mock_questions_db["get_teacher_by_user_id"].return_value = MagicMock(id="teacher_001")
        mock_questions_db["get_question_by_id"].return_value = None

        response = await client.patch(
            "/api/v1/questions/clxfake_q_999",
            json={"text": "Updated text"},
        )
        assert response.status_code == 404
        assert "Question not found" in response.json()["detail"]

    async def test_patch_not_teacher(self, client, override_auth, mock_questions_db):
        override_auth(role="STUDENT")

        response = await client.patch(
            "/api/v1/questions/clxfake_q_001",
            json={"text": "Updated text"},
        )
        assert response.status_code == 403

    async def test_delete_success(self, client, override_auth, mock_questions_db):
        override_auth(role="TEACHER")
        mock_questions_db["get_teacher_by_user_id"].return_value = MagicMock(id="teacher_001")
        fake_question = make_fake_question()
        mock_questions_db["get_question_by_id"].return_value = fake_question

        response = await client.delete(f"/api/v1/questions/{fake_question.id}")
        assert response.status_code == 204
        mock_questions_db["delete_question"].assert_called_once_with(fake_question.id)

    async def test_delete_not_found(self, client, override_auth, mock_questions_db):
        override_auth(role="TEACHER")
        mock_questions_db["get_teacher_by_user_id"].return_value = MagicMock(id="teacher_001")
        mock_questions_db["get_question_by_id"].return_value = None

        response = await client.delete("/api/v1/questions/clxfake_q_999")
        assert response.status_code == 404
        assert "Question not found" in response.json()["detail"]
