"""Integration tests for the complete AI Question Paper Import lifecycle."""

import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clients.cohere_client import CohereClient
from app.core.models import (
    Exam,
    Question,
    QuestionImport,
    QuestionImportStatus,
    QuestionOption,
    Role,
)
from app.imports.service import process_question_import
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "question_papers")

MOCK_COHERE_SUCCESS_RESPONSE = {
    "title": "General Science Quiz",
    "subject": "SCIENCE",
    "total_marks": 20.0,
    "duration_minutes": 30,
    "instructions": ["Answer all questions."],
    "questions": [
        {
            "question_number": "1",
            "question_type": "MULTIPLE_CHOICE",
            "text": "What is the chemical symbol for Water?",
            "marks": 2.0,
            "section": "Section A",
            "options": [
                {"label": "A", "text": "H2O", "is_correct": None},
                {"label": "B", "text": "CO2", "is_correct": None},
                {"label": "C", "text": "O2", "is_correct": None},
                {"label": "D", "text": "NaCl", "is_correct": None},
            ],
            "confidence": "HIGH",
            "warnings": [],
        },
        {
            "question_number": "2",
            "question_type": "MULTIPLE_CHOICE",
            "text": "Which planet is known as the Red Planet?",
            "marks": 2.0,
            "section": "Section A",
            "options": [
                {"label": "A", "text": "Venus", "is_correct": None},
                {"label": "B", "text": "Mars", "is_correct": None},
                {"label": "C", "text": "Jupiter", "is_correct": None},
                {"label": "D", "text": "Saturn", "is_correct": None},
            ],
            "confidence": "HIGH",
            "warnings": [],
        },
    ],
    "warnings": [],
}


@pytest.fixture
def mock_cohere_client():
    client = CohereClient(api_key="mock-key")
    mock_chat_response = MagicMock()
    mock_chat_response.message.content = [
        MagicMock(text=json.dumps(MOCK_COHERE_SUCCESS_RESPONSE))
    ]
    mock_chat_response.usage.tokens.input_tokens = 250
    mock_chat_response.usage.tokens.output_tokens = 180

    mock_co_instance = MagicMock()
    mock_co_instance.chat.return_value = mock_chat_response
    client._client = mock_co_instance
    return client


@pytest.mark.asyncio
async def test_question_import_authorization(
    auth_client_factory, db_session: AsyncSession
):
    """Verify role authorization gates on question imports."""
    # Setup owner teacher and unrelated teacher
    principal_user = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p1@dev.local")
    school = await create_school_factory(db_session, creator_user=principal_user, school_code="SCH-IMP-1")

    owner_user = await create_user_factory(db_session, role=Role.TEACHER, email="owner@dev.local")
    owner_teacher = await create_teacher_factory(db_session, user=owner_user, school=school)

    unrelated_user = await create_user_factory(db_session, role=Role.TEACHER, email="unrelated@dev.local")
    await create_teacher_factory(db_session, user=unrelated_user, school=school)

    student_user = await create_user_factory(db_session, role=Role.STUDENT, email="student@dev.local")

    exam = await create_exam_factory(db_session, teacher=owner_teacher, name="Math Midterm")
    await db_session.commit()

    valid_pdf_path = os.path.join(FIXTURES_DIR, "simple_mcq.pdf")
    with open(valid_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. Student cannot upload -> 403
    student_client = await auth_client_factory(student_user)
    res_student = await student_client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res_student.status_code == 403

    # 2. Unrelated teacher cannot upload to another teacher's exam -> 403
    unrelated_client = await auth_client_factory(unrelated_user)
    res_unrelated = await unrelated_client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res_unrelated.status_code == 403

    # 3. Owner teacher can upload -> 202
    owner_client = await auth_client_factory(owner_user)
    res_owner = await owner_client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res_owner.status_code == 202
    data = res_owner.json()
    assert data["status"] == "UPLOADED"
    assert data["examId"] == exam.id
    assert data["originalFileName"] == "simple_mcq.pdf"


@pytest.mark.asyncio
async def test_full_question_import_and_confirmation_lifecycle(
    auth_client_factory, db_session: AsyncSession, mock_cohere_client
):
    """Test full import flow: Upload -> Background Worker -> Review Draft -> Confirm -> Verify Idempotency."""
    principal_user = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p2@dev.local")
    school = await create_school_factory(db_session, creator_user=principal_user, school_code="SCH-IMP-2")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="teacher2@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher, name="Science Assessment")
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    valid_pdf_path = os.path.join(FIXTURES_DIR, "simple_mcq.pdf")
    with open(valid_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. Upload
    upload_res = await client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 202
    import_id = upload_res.json()["id"]

    # 2. Execute background processing job with mocked Cohere
    await process_question_import(import_id, cohere_client=mock_cohere_client)

    # 3. Check status endpoint (NEEDS_REVIEW)
    status_res = await client.get(f"/api/v1/question-imports/{import_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "NEEDS_REVIEW"
    assert status_data["questionCount"] == 2
    assert len(status_data["questions"]) == 2
    assert status_data["questions"][0]["text"] == "What is the chemical symbol for Water?"
    # Answer key not guessed (None)
    for opt in status_data["questions"][0]["options"]:
        assert opt["is_correct"] is None

    # 4. Teacher edits draft (PATCH)
    edit_payload = {
        "title": "Edited Science Quiz",
        "questions": [
            {
                "question_number": "1",
                "question_type": "MULTIPLE_CHOICE",
                "text": "What is the chemical formula of Pure Water?",  # edited wording
                "marks": 3.0,  # updated marks
                "section": "Section A",
                "options": [
                    {"label": "A", "text": "H2O", "is_correct": False},
                    {"label": "B", "text": "CO2", "is_correct": False},
                ],
                "confidence": "HIGH",
                "warnings": [],
            },
            status_data["questions"][1],  # Q2 unchanged
        ],
    }
    patch_res = await client.patch(
        f"/api/v1/question-imports/{import_id}",
        json=edit_payload,
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["title"] == "Edited Science Quiz"
    assert patched_data["questions"][0]["text"] == "What is the chemical formula of Pure Water?"
    assert patched_data["questions"][0]["marks"] == 3.0

    # 5. Confirm import
    confirm_res = await client.post(f"/api/v1/question-imports/{import_id}/confirm")
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["status"] == "COMPLETED"
    assert confirm_data["createdQuestionsCount"] == 2

    # Verify questions and options were inserted into database
    q_stmt = select(Question).where(Question.examId == exam.id).order_by(Question.questionNumber)
    db_questions = (await db_session.execute(q_stmt)).scalars().all()
    assert len(db_questions) == 2
    assert db_questions[0].text == "What is the chemical formula of Pure Water?"
    assert db_questions[0].marks == 3

    opt_stmt = select(QuestionOption).where(QuestionOption.questionId == db_questions[0].id)
    db_options = (await db_session.execute(opt_stmt)).scalars().all()
    assert len(db_options) == 2

    # 6. Idempotency test: Confirming a second time must NOT create duplicate questions
    confirm_twice_res = await client.post(f"/api/v1/question-imports/{import_id}/confirm")
    assert confirm_twice_res.status_code == 200
    twice_data = confirm_twice_res.json()
    assert twice_data["status"] == "COMPLETED"
    assert twice_data["createdQuestionsCount"] == 0

    # Verify count is still exactly 2
    total_q_count = (
        await db_session.execute(
            select(func.count(Question.id)).where(Question.examId == exam.id)
        )
    ).scalar()
    assert total_q_count == 2


@pytest.mark.asyncio
async def test_confirm_rejects_unknown_question_type(
    auth_client_factory, db_session: AsyncSession
):
    """Verify that questions with UNKNOWN type require teacher correction before confirmation."""
    principal_user = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p3@dev.local")
    school = await create_school_factory(db_session, creator_user=principal_user, school_code="SCH-IMP-3")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="teacher3@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher, name="Draft Exam")

    # Create import in NEEDS_REVIEW with an UNKNOWN question
    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="test.pdf",
        fileType="application/pdf",
        fileSize=100,
        filePath="fake/path.pdf",
        status=QuestionImportStatus.NEEDS_REVIEW,
        validatedExtraction={
            "title": "Exam",
            "questions": [
                {
                    "question_number": "1",
                    "question_type": "UNKNOWN",
                    "text": "Unclear question structure",
                    "marks": 1.0,
                    "options": [],
                    "confidence": "LOW",
                    "warnings": ["Could not classify type"],
                }
            ],
            "warnings": [],
        },
    )
    db_session.add(import_rec)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    confirm_res = await client.post(f"/api/v1/question-imports/{import_rec.id}/confirm")
    assert confirm_res.status_code == 400
    assert "UNKNOWN question type" in confirm_res.json()["detail"]


@pytest.mark.asyncio
async def test_confirm_rejects_missing_marks(
    auth_client_factory, db_session: AsyncSession
):
    """Verify that questions with missing marks require teacher assignment before confirmation."""
    principal_user = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p4@dev.local")
    school = await create_school_factory(db_session, creator_user=principal_user, school_code="SCH-IMP-4")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="teacher4@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher, name="Draft Exam 2")

    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="test.pdf",
        fileType="application/pdf",
        fileSize=100,
        filePath="fake/path.pdf",
        status=QuestionImportStatus.NEEDS_REVIEW,
        validatedExtraction={
            "title": "Exam",
            "questions": [
                {
                    "question_number": "1",
                    "question_type": "SHORT_ANSWER",
                    "text": "Describe gravity.",
                    "marks": None,  # missing marks
                    "options": [],
                    "confidence": "MEDIUM",
                    "warnings": ["Marks missing"],
                }
            ],
            "warnings": [],
        },
    )
    db_session.add(import_rec)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    confirm_res = await client.post(f"/api/v1/question-imports/{import_rec.id}/confirm")
    assert confirm_res.status_code == 400
    assert "missing positive marks" in confirm_res.json()["detail"]


@pytest.mark.asyncio
async def test_list_exam_imports(
    auth_client_factory, db_session: AsyncSession
):
    """Verify listing previous question imports for an exam."""
    principal_user = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p5@dev.local")
    school = await create_school_factory(db_session, creator_user=principal_user, school_code="SCH-IMP-5")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="teacher5@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher, name="List Exam")

    import_rec1 = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="paper1.pdf",
        fileType="application/pdf",
        fileSize=500,
        filePath="fake/paper1.pdf",
        status=QuestionImportStatus.COMPLETED,
    )
    import_rec2 = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="paper2.pdf",
        fileType="application/pdf",
        fileSize=600,
        filePath="fake/paper2.pdf",
        status=QuestionImportStatus.UPLOADED,
    )
    db_session.add_all([import_rec1, import_rec2])
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    list_res = await client.get(f"/api/v1/exams/{exam.id}/question-imports")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 2
    filenames = {i["originalFileName"] for i in items}
    assert "paper1.pdf" in filenames
    assert "paper2.pdf" in filenames
