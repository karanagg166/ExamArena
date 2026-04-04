from typing import Any, cast

import app.core.database as db
from app.exams.schemas import (
    ExamCreateRequest,
    ExamResponse,
    ExamUpdateRequest,
)

EXAM_INCLUDE = {
    "teacher": {
        "include": {
            "user": True,
            "school": True,
        }
    },
    "questions": {
        "include": {
            "options": True
        }
    }
}


async def create_exam(exam_data: ExamCreateRequest, teacher_id: str) -> ExamResponse:
    questions_payload = []

    if exam_data.questions:
        for q in exam_data.questions:
            options = []
            if q.options:
                options = [
                    {
                        "text": o.text,
                        "optionNumber": o.optionNumber,
                        "isCorrect": o.isCorrect,
                        "imageUrl": o.imageUrl,
                    }
                    for o in q.options
                ]

            q_dict = {
                "text": q.text,
                "marks": q.marks,
                "questionNumber": q.questionNumber,
                "questionType": q.questionType,
                "imageUrl": q.imageUrl,
                "wordLimit": q.wordLimit,
                "explanation": q.explanation,
                "section": q.section,
            }

            if options:
                q_dict["options"] = {"create": options}

            questions_payload.append(q_dict)

    data = {
        "name": exam_data.name,
        "description": exam_data.description,
        "scheduledAt": exam_data.scheduledAt,
        "duration": exam_data.duration,
        "maxMarks": exam_data.maxMarks,
        "instructions": exam_data.instructions,
        "isPublished": exam_data.isPublished,
        "type": exam_data.type,
        "teacherId": teacher_id,
    }

    if exam_data.subject:
        data["subject"] = exam_data.subject

    if questions_payload:
        data["questions"] = {"create": questions_payload}

    try:
        exam = await db.prisma.exam.create(
            data=data, # type: ignore
            include=EXAM_INCLUDE, # pyright: ignore[reportArgumentType]
        )
    except Exception:
        # Handle transient "connection closed" states by reconnecting once.
        try:
            await db.prisma.disconnect()
        except Exception:
            pass
        await db.prisma.connect()
        exam = await db.prisma.exam.create(
            data=data, # type: ignore
            include=EXAM_INCLUDE, # pyright: ignore[reportArgumentType]
        )

    return ExamResponse.model_validate(exam)


async def get_exam_by_id(exam_id: str) -> ExamResponse | None:
    exam = await db.prisma.exam.find_unique(
        where={"id": exam_id},
        include=EXAM_INCLUDE, # type: ignore
    )
    return ExamResponse.model_validate(exam) if exam else None


async def get_exams_by_teacher(teacher_id: str) -> list[ExamResponse]:
    exams = await db.prisma.exam.find_many(
        where={"teacherId": teacher_id},
        include=EXAM_INCLUDE, # type: ignore
    )
    return [ExamResponse.model_validate(e) for e in exams]


async def get_published_exams(
    name=None,
    exam_type=None,
    teacher_name=None,
    school_name=None,
    subject=None,
    school_id=None,
):
    where = {"isPublished": True}

    if name:
        where["name"] = {"contains": name, "mode": "insensitive"} # type: ignore

    if exam_type:
        where["type"] = exam_type

    if subject:
        where["subject"] = subject

    teacher_filter = {}

    if teacher_name:
        teacher_filter["user"] = {
            "name": {"contains": teacher_name, "mode": "insensitive"}
        }

    if school_name:
        teacher_filter["school"] = {
            "name": {"contains": school_name, "mode": "insensitive"}
        }

    if school_id:
        teacher_filter["schoolId"] = school_id

    if teacher_filter:
        where["teacher"] = teacher_filter # type: ignore

    exams = await db.prisma.exam.find_many(
        where=where, # type: ignore
        include=EXAM_INCLUDE, # pyright: ignore[reportArgumentType]
    )

    return [ExamResponse.model_validate(e) for e in exams]

async def get_published_exams_for_student(student_id: str, school_id: str, name=None, exam_type=None, subject=None) -> list[dict]:
    where = {
        "isPublished": True,
        "teacher": {
            "schoolId": school_id
        }
    }

    if name:
        where["name"] = {"contains": name, "mode": "insensitive"}

    if exam_type:
        where["type"] = exam_type

    if subject:
        where["subject"] = subject

    exams = await db.prisma.exam.find_many(
        where=where, # type: ignore
        include=cast(
            Any,
            {
                "teacher": {"include": {"user": True, "school": True}},
                "questions": {"include": {"options": True}},
                "studentExams": {
                    "where": {"studentId": student_id}
                }
            },
        ),
    )

    results = []
    for e in exams:
        # Convert Prisma model to dict
        e_dict = e.model_dump()

        # Add student status metadata
        student_exams = getattr(e, "studentExams", []) or []
        if student_exams and len(student_exams) > 0:
            e_dict["studentStatus"] = student_exams[0].status
            e_dict["attemptId"] = student_exams[0].id
        else:
            e_dict["studentStatus"] = "NOT_ATTEMPTED"
            e_dict["attemptId"] = None

        results.append(e_dict)

    return results


async def update_exam(exam_id: str, update_data: ExamUpdateRequest) -> ExamResponse | None:
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"questions"})

    async with db.prisma.tx() as tx:
        await tx.exam.update(
            where={"id": exam_id},
            data=update_dict, # type: ignore
        )

    return await get_exam_by_id(exam_id)
