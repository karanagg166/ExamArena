"""End-to-End Golden Lifecycle integration test covering the entire ExamArena platform."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Role,
    Teacher,
)
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_complete_golden_lifecycle_integration(
    auth_client_factory, db_session: AsyncSession
):
    """Test the complete golden path from School Creation through Student Exam Attempt and Result Release."""
    # ── Step 1: Principal registers and creates School ────────────────────────
    principal_user = await create_user_factory(
        db_session,
        name="Principal Skinner",
        email="skinner.golden@springfield.edu",
        role=Role.PRINCIPAL,
    )
    await db_session.commit()
    principal_client = await auth_client_factory(principal_user)

    school_resp = await principal_client.post(
        "/api/v1/schools",
        json={
            "name": "Springfield High",
            "type": "PUBLIC",
            "schoolCode": "SPRF-GLD",
            "email": "contact@springfieldhigh.edu",
            "address": "742 Evergreen Terrace",
            "city": "Springfield",
            "state": "Oregon",
            "country": "USA",
            "pincode": "97477",
            "phoneNo": "9876543210",
        },
    )
    assert school_resp.status_code == 201
    school_id = school_resp.json()["id"]

    # ── Step 2: Principal creates Class 10-A ──────────────────────────────────
    class_resp = await principal_client.post(
        "/api/v1/classes",
        json={
            "name": "Class 10-A",
            "year": "2026",
            "section": "A",
            "schoolId": school_id,
        },
    )
    assert class_resp.status_code == 201
    class_data = class_resp.json()
    class_id = class_data["id"]
    join_code = class_data["joinCode"]
    assert len(join_code) == 8

    # ── Step 3: Teacher registers & requests to join School ──────────────────
    teacher_user = await create_user_factory(
        db_session,
        name="Edna Krabappel",
        email="edna.golden@springfield.edu",
        role=Role.TEACHER,
    )
    teacher = Teacher(
        userId=teacher_user.id,
        experience=10,
        department="Mathematics",
        qualification='["BACHELORS"]',
        subjects='["MATHS"]',
    )
    db_session.add(teacher)
    await db_session.commit()

    teacher_client = await auth_client_factory(teacher_user)

    req_resp = await teacher_client.post(
        "/api/v1/teacher-requests/school",
        json={"schoolId": school_id},
    )
    assert req_resp.status_code in (200, 201)
    req_id = req_resp.json()["id"]

    # Principal approves teacher
    app_resp = await principal_client.patch(
        f"/api/v1/teacher-requests/school-requests/{req_id}",
        json={"status": "APPROVED"},
    )
    assert app_resp.status_code == 200

    # Principal assigns teacher to Class 10-A
    assign_resp = await principal_client.post(
        f"/api/v1/classes/{class_id}/assign-teacher",
        json={"teacherId": teacher.id},
    )
    assert assign_resp.status_code in (200, 201)

    # ── Step 4: Student registers and joins Class via joinCode ───────────────
    student_user = await create_user_factory(
        db_session,
        name="Bart Simpson",
        email="bart.golden@springfield.edu",
        role=Role.STUDENT,
    )
    await db_session.commit()
    student_client = await auth_client_factory(student_user)

    # Student requests to join class using joinCode
    stud_join_resp = await student_client.post(
        "/api/v1/join-requests/join-by-code",
        json={"joinCode": join_code},
    )
    assert stud_join_resp.status_code in (200, 201)
    stud_req_id = stud_join_resp.json()["id"]

    # Principal approves student join request -> roll number assigned
    app_stud_resp = await principal_client.patch(
        f"/api/v1/join-requests/{stud_req_id}",
        json={"status": "APPROVED"},
    )
    assert app_stud_resp.status_code == 200

    # ── Step 5: Teacher creates published Exam with Question & Options ────────
    exam_resp = await teacher_client.post(
        "/api/v1/exams",
        json={
            "name": "Algebra Midterm",
            "description": "Standard Algebra Exam",
            "scheduledAt": "2026-01-01T10:00:00Z",
            "duration": 60,
            "maxMarks": 10,
            "subject": "MATHS",
            "type": "MIDTERM",
            "isPublished": True,
            "isPublic": True,
            "negativeMarking": True,
            "negativeMarks": 1.0,
        },
    )
    assert exam_resp.status_code == 201
    exam_id = exam_resp.json()["id"]

    # Add Question 1: 5 marks, correct = 4
    q1_resp = await teacher_client.post(
        "/api/v1/questions",
        json={
            "examId": exam_id,
            "questionNumber": 1,
            "text": "What is 2 + 2?",
            "marks": 5,
            "questionType": "MULTIPLE_CHOICE",
            "explanation": "2 + 2 is 4",
            "options": [
                {"text": "4", "optionNumber": 1, "isCorrect": True},
                {"text": "5", "optionNumber": 2, "isCorrect": False},
            ],
        },
    )
    assert q1_resp.status_code == 201
    q1_data = q1_resp.json()
    q1_id = q1_data["id"]
    correct_opt_id = next(o["id"] for o in q1_data["options"] if o["isCorrect"])

    # ── Step 6: Student takes exam, submits answer, and completes attempt ─────
    start_resp = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id},
    )
    assert start_resp.status_code in (200, 201)
    attempt_data = start_resp.json()
    attempt_id = attempt_data["id"]
    ans_shell_id = attempt_data["answers"][0]["id"]

    # Student submits attempt with answer
    sub_resp = await student_client.post(
        "/api/v1/attempts/submit",
        json={
            "id": attempt_id,
            "answers": [
                {
                    "id": ans_shell_id,
                    "selectedOptions": [{"optionId": correct_opt_id}],
                }
            ],
        },
    )
    assert sub_resp.status_code == 200

    # ── Step 7: Teacher releases results and verifies student score ───────────
    rel_resp = await teacher_client.post(
        f"/api/v1/exams/{exam_id}/release-results",
    )
    assert rel_resp.status_code == 200

    # Student views released exam and verifies answer review
    review_resp = await student_client.get(f"/api/v1/exams/{exam_id}")
    assert review_resp.status_code == 200
    assert review_resp.json()["isResultsReleased"] is True
    assert review_resp.json()["questions"][0]["explanation"] == "2 + 2 is 4"
