from app.exams.schemas import (
    ExamCreateRequest,
    ExamResponse,
    ExamType,
    ExamUpdateRequest,
    Subject,
)
import app.core.database as db

EXAM_INCLUDE = {
    "teacher": {
        "include": {
            "user": True,
            "school": True
        }
    },
    "questions": {
        "include": {
            "options": True
        }
    }
}

async def create_exam(exam_data: ExamCreateRequest, teacher_id: str) -> ExamResponse:
    # Prepare nested payload for questions and their options
    questions_payload = []
    if exam_data.questions:
        for q in exam_data.questions:
            opts = []
            if q.options:
                opts = [{"text": o.text, "optionNumber": o.optionNumber, "isCorrect": o.isCorrect, "imageUrl": o.imageUrl} for o in q.options]

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
            if opts:
                q_dict["options"] = {"create": opts}
            questions_payload.append(q_dict)

    create_data = {
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
        create_data["subject"] = exam_data.subject

    if questions_payload:
        create_data["questions"] = {"create": questions_payload}

    exam = await db.prisma.exam.create(
        data=create_data, # type: ignore
        include=EXAM_INCLUDE # type: ignore
    )
    return ExamResponse.model_validate(exam)

async def get_exam_by_id(exam_id: str) -> ExamResponse | None:
    exam = await db.prisma.exam.find_unique(
        where={"id": exam_id},
        include=EXAM_INCLUDE # type: ignore
    )
    return ExamResponse.model_validate(exam) if exam else None

async def get_exams_by_teacher(teacher_id: str) -> list[ExamResponse]:
    exams = await db.prisma.exam.find_many(
        where={"teacherId": teacher_id},
        include=EXAM_INCLUDE # type: ignore
    )
    return [ExamResponse.model_validate(e) for e in exams]

async def get_published_exams(
    name: str | None = None,
    exam_type: ExamType | None = None,
    teacher_name: str | None = None,
    school_name: str | None = None,
    subject: Subject | None = None,
) -> list[ExamResponse]:
    # Construct conditions
    where = {"isPublished": True} # type: ignore
    if name:
        where["name"] = {"contains": name, "mode": "insensitive"}
    if exam_type:
        where["type"] = exam_type
    if subject:
        where["subject"] = subject
    
    if teacher_name or school_name:
        where["teacher"] = {}
        if teacher_name:
            where["teacher"]["user"] = {"name": {"contains": teacher_name, "mode": "insensitive"}}
        if school_name:
            where["teacher"]["school"] = {"name": {"contains": school_name, "mode": "insensitive"}}

    exams = await db.prisma.exam.find_many(
        where=where,
        include=EXAM_INCLUDE
    )
    return [ExamResponse.model_validate(e) for e in exams]

async def update_exam(exam_id: str, update_data: ExamUpdateRequest) -> ExamResponse | None:
    # 1. Update basic exam fields first
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"id", "questions"})
    
    async with db.prisma.tx() as transaction:
        await transaction.exam.update(
            where={"id": exam_id},
            data=update_dict, # type: ignore
        )

        if update_data.questions is not None:
            # A. Get current questions to find deletions
            current_questions = await transaction.question.find_many(where={"examId": exam_id})
            current_q_ids = {q.id for q in current_questions}
            incoming_q_ids = {q.id for q in update_data.questions if q.id}
            
            # Deletions
            to_delete_q = current_q_ids - incoming_q_ids
            if to_delete_q:
                await transaction.question.delete_many(where={"id": {"in": list(to_delete_q)}})

            # B. Process Upserts (New or Updated)
            for q_data in update_data.questions:
                q_dict = q_data.model_dump(exclude_unset=True, exclude={"options", "id"})
                
                if q_data.id:
                    # Update Existing Question
                    await transaction.question.update(
                        where={"id": q_data.id},
                        data=q_dict # type: ignore
                    )
                    
                    if q_data.options is not None:
                        # Handle Nested Options Deletion/Upsert
                        current_options = await transaction.questionoption.find_many(where={"questionId": q_data.id})
                        current_o_ids = {o.id for o in current_options}
                        incoming_o_ids = {o.id for o in q_data.options if o.id}
                        
                        to_delete_o = current_o_ids - incoming_o_ids
                        if to_delete_o:
                            await transaction.questionoption.delete_many(where={"id": {"in": list(to_delete_o)}})
                            
                        for o_data in q_data.options:
                            o_dict = o_data.model_dump(exclude_unset=True, exclude={"id"})
                            if o_data.id:
                                await transaction.questionoption.update(
                                    where={"id": o_data.id},
                                    data=o_dict # type: ignore
                                )
                            else:
                                o_dict["questionId"] = q_data.id
                                await transaction.questionoption.create(data=o_dict) # type: ignore
                else:
                    # Create New Question
                    q_dict["examId"] = exam_id
                    new_q = await transaction.question.create(
                        data=q_dict # type: ignore
                    )
                    # Create New Options for New Question
                    if q_data.options:
                        for o_data in q_data.options:
                            o_dict = o_data.model_dump(exclude_unset=True, exclude={"id"})
                            o_dict["questionId"] = new_q.id
                            await transaction.questionoption.create(data=o_dict) # type: ignore

    # Return refreshed exam with relations
    return await get_exam_by_id(exam_id)
