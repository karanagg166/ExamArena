"""API-level integration tests for /api/v1/exams/{exam_id}/answer-key-imports and /api/v1/answer-key-imports/*."""

import io
from unittest.mock import AsyncMock, patch
import pytest

from app.core.models import (
    AnswerKeyImportStatus,
    QuestionType,
    Role,
)
from tests.factories.exam_factory import (
    create_exam_factory,
    create_question_factory,
)
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_unauthenticated_cannot_import_answer_key(client):
    res = await client.post(
        "/api/v1/exams/non-existent-exam/answer-key-imports",
        files={"file": ("key.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_import_answer_key(client, override_auth):
    override_auth(role="STUDENT")
    res = await client.post(
        "/api/v1/exams/some-exam-id/answer-key-imports",
        files={"file": ("key.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_answer_key_upload_missing_file_422(auth_client_factory, db_session):
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak1@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-1")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak1@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    res = await client.post(f"/api/v1/exams/{exam.id}/answer-key-imports")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_answer_key_upload_invalid_mime_rejected(auth_client_factory, db_session):
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak2@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-2")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak2@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    fake_content = b"NOT A VALID PDF OR IMAGE"
    res = await client.post(
        f"/api/v1/exams/{exam.id}/answer-key-imports",
        files={"file": ("fake.pdf", io.BytesIO(fake_content), "application/pdf")},
    )
    assert res.status_code == 415


@pytest.mark.asyncio
async def test_answer_key_upload_success_202(auth_client_factory, db_session):
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak3@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-3")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak3@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    valid_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"

    with patch("app.answer_keys.service.process_answer_key_import", new_callable=AsyncMock) as mock_worker:
        res = await client.post(
            f"/api/v1/exams/{exam.id}/answer-key-imports",
            files={"file": ("valid_key.pdf", io.BytesIO(valid_pdf), "application/pdf")},
        )
        assert res.status_code == 202
        body = res.json()
        assert body["examId"] == exam.id
        assert body["status"] == "UPLOADED"
        assert body["originalFileName"] == "valid_key.pdf"
        assert "id" in body


@pytest.mark.asyncio
async def test_answer_key_draft_edit_and_confirmation(auth_client_factory, db_session):
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak4@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-4")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak4@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    # Create exam question 1 (MCQ)
    q1 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=1,
        text="What is the chemical symbol for water?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        marks=2,
        options_data=[
            {"text": "CO2", "isCorrect": False},
            {"text": "H2O", "isCorrect": False},
        ],
    )

    # Create exam question 2 (SHORT_ANSWER)
    q2 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=2,
        text="Define kinetic energy.",
        question_type=QuestionType.SHORT_ANSWER,
        marks=3,
        explanation=None,
    )
    await db_session.commit()
    q1_id = q1.id
    q2_id = q2.id

    from sqlalchemy import select
    from app.core.models import Question, QuestionOption

    opts_res = await db_session.execute(
        select(QuestionOption).where(QuestionOption.questionId == q1_id).order_by(QuestionOption.optionNumber)
    )
    opts = list(opts_res.scalars().all())
    opt1_a = opts[0]
    opt1_b = opts[1]

    # Create AnswerKeyImport directly in NEEDS_REVIEW
    from app.answer_keys.crud import create_answer_key_import, update_answer_key_import_success
    from app.core.models import AnswerKeyImportSourceType

    import_rec = await create_answer_key_import(
        exam_id=exam.id,
        teacher_id=teacher.id,
        original_file_name="chem_key.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_path="mock_path.pdf",
        source_type=AnswerKeyImportSourceType.PDF_TEXT,
        session=db_session,
    )

    validated_payload = {
        "import_id": import_rec.id,
        "exam_id": exam.id,
        "matched_count": 2,
        "ambiguous_count": 0,
        "unmatched_count": 0,
        "total_answers": 2,
        "answers": [
            {
                "question_reference": "1",
                "status": "MATCHED",
                "matched_question_id": q1.id,
                "matched_question_number": 1,
                "matched_option_id": opt1_b.id,
                "selected_option": "B",
                "explanation": "Water is composed of hydrogen and oxygen",
                "confidence": "HIGH",
                "warnings": [],
                "rubric": [],
                "candidate_question_ids": [],
            },
            {
                "question_reference": "2",
                "status": "MATCHED",
                "matched_question_id": q2.id,
                "matched_question_number": 2,
                "reference_answer": "Energy possessed by a body due to its motion: KE = 1/2 mv^2",
                "rubric": [
                    {"criterion": "Definition", "marks": 1.5},
                    {"criterion": "Formula", "marks": 1.5},
                ],
                "explanation": "Standard physics textbook definition",
                "confidence": "HIGH",
                "warnings": [],
                "candidate_question_ids": [],
            },
        ],
        "warnings": [],
    }

    await update_answer_key_import_success(
        import_id=import_rec.id,
        source_type=AnswerKeyImportSourceType.PDF_TEXT,
        extracted_text="1. B\n2. KE = 1/2 mv^2",
        raw_extraction=validated_payload,
        validated_extraction=validated_payload,
        session=db_session,
    )
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    # 1. Fetch import details
    get_res = await client.get(f"/api/v1/answer-key-imports/{import_rec.id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "NEEDS_REVIEW"
    assert len(get_res.json()["answers"]) == 2

    # 2. Confirm import
    confirm_res = await client.post(
        f"/api/v1/answer-key-imports/{import_rec.id}/confirm",
        json={"overwriteExistingAnswers": False},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "COMPLETED"
    assert confirm_res.json()["updatedQuestionsCount"] == 2

    # 3. Verify in database that questions and options were updated
    opts_updated_res = await db_session.execute(
        select(QuestionOption)
        .where(QuestionOption.questionId == q1_id)
        .order_by(QuestionOption.optionNumber)
        .execution_options(populate_existing=True)
    )
    opts_updated = list(opts_updated_res.scalars().all())
    assert opts_updated[0].isCorrect is False
    assert opts_updated[1].isCorrect is True

    q2_res = await db_session.execute(
        select(Question)
        .where(Question.id == q2_id)
        .execution_options(populate_existing=True)
    )
    q2_updated = q2_res.scalar_one()
    assert q2_updated.referenceAnswer == "Energy possessed by a body due to its motion: KE = 1/2 mv^2"
    assert len(q2_updated.gradingRubric) == 2
    assert q2_updated.explanation == "Standard physics textbook definition"
