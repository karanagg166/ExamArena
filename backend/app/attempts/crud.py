import app.core.database as db
from app.attempts.schemas import StudentExamCreate, StudentExamSubmit, AttemptStatus, StudentExamResponse
from app.students.crud import get_student_by_user_id
from datetime import datetime, timezone

async def start_exam_attempt(attempt_data: StudentExamCreate, user_id: str) -> StudentExamResponse:
    student = await get_student_by_user_id(user_id)
    if not student:
        raise ValueError("Only students can start an exam")
        
    exam = await db.prisma.exam.find_unique(where={"id": attempt_data.examId}, include={"questions": True})
    if not exam:
        raise ValueError("Exam not found")

    # Check for existing attempt
    existing = await db.prisma.studentexam.find_unique(
        where={"studentId_examId": {"studentId": student.id, "examId": exam.id}},
        include={"answers": {"include": {"selectedOptions": True}}}
    )
    if existing:
        return StudentExamResponse.model_validate(existing)

    # Create empty answers for all questions
    answers_payload = [
        {
            "questionId": q.id,
            "questionType": q.questionType,
            "gradingStatus": "PENDING"
        }
        for q in exam.questions
    ] if exam.questions else []

    return await db.prisma.studentexam.create(
        data={
            "studentId": student.id,
            "examId": exam.id,
            "status": AttemptStatus.IN_PROGRESS,
            "startedAt": datetime.now(timezone.utc),
            "answers": {
                "create": answers_payload
            } if answers_payload else None
        },
        include={
            "answers": {
                "include": {
                    "selectedOptions": True
                }
            }
        }
    )
    return StudentExamResponse.model_validate(attempt_model)

async def get_attempt_by_id(attempt_id: str) -> StudentExamResponse | None:
    attempt_model = await db.prisma.studentexam.find_unique(
        where={"id": attempt_id},
        include={
            "answers": {
                "include": {
                    "selectedOptions": True
                }
            }
        }
    )
    return StudentExamResponse.model_validate(attempt_model) if attempt_model else None

async def submit_exam_attempt(submit_data: StudentExamSubmit, user_id: str) -> StudentExamResponse:
    student = await get_student_by_user_id(user_id)
    attempt = await get_attempt_by_id(submit_data.id)
    if not attempt:
        raise ValueError("Attempt not found")
        
    if student and attempt.studentId != student.id:
        raise ValueError("Not authorized to submit this attempt")

    for ans in submit_data.answers:
        update_data = {}
        if ans.textAnswer is not None:
            update_data["textAnswer"] = ans.textAnswer
            
        opts_payload = {}
        if ans.selectedOptions is not None:
            opts = [{"optionId": o.optionId} for o in ans.selectedOptions]
            opts_payload = {
                "deleteMany": {},
                "create": opts
            }
        
        if opts_payload:
            update_data["selectedOptions"] = opts_payload
            
        if update_data:
            # Update individual answer item
            await db.prisma.studentexamanswer.update(
                where={"id": ans.id},
                data=update_data
            )

    updated_attempt = await db.prisma.studentexam.update(
        where={"id": submit_data.id},
        data={
            "status": AttemptStatus.SUBMITTED,
            "submittedAt": datetime.now(timezone.utc)
        },
        include={
            "answers": {
                "include": {
                    "selectedOptions": True
                }
            }
        }
    )
    return StudentExamResponse.model_validate(updated_attempt)
