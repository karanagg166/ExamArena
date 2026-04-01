import app.core.database as db
from app.questions.schemas import QuestionCreateRequest, QuestionUpdateRequest, QuestionResponse

async def create_question(question_data: QuestionCreateRequest) -> QuestionResponse:
    opts = []
    if question_data.options:
        opts = [{"text": o.text, "optionNumber": o.optionNumber, "isCorrect": o.isCorrect, "imageUrl": o.imageUrl} for o in question_data.options]
        
    create_data = {
        "text": question_data.text,
        "marks": question_data.marks,
        "questionNumber": question_data.questionNumber,
        "questionType": question_data.questionType,
        "imageUrl": question_data.imageUrl,
        "wordLimit": question_data.wordLimit,
        "explanation": question_data.explanation,
        "section": question_data.section,
        "examId": question_data.examId,
    }
    
    if opts:
        create_data["options"] = {"create": opts}

    question = await db.prisma.question.create(
        data=create_data,
        include={"options": True}
    )
    return QuestionResponse.model_validate(question)

async def update_question(question_id: str, update_data: QuestionUpdateRequest) -> QuestionResponse | None:
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"id", "options"})
    
    opts_payload = {}
    if update_data.options is not None:
        opts = [{"text": o.text, "optionNumber": o.optionNumber, "isCorrect": o.isCorrect, "imageUrl": o.imageUrl} for o in update_data.options]
        # We replace all options safely
        opts_payload = {
            "deleteMany": {}, # Delete all old options
            "create": opts # Insert all new options
        }

    if opts_payload:
        update_dict["options"] = opts_payload

    updated = await db.prisma.question.update(
        where={"id": question_id},
        data=update_dict,
        include={"options": True}
    )
    return QuestionResponse.model_validate(updated) if updated else None

async def get_question_by_id(question_id: str) -> QuestionResponse | None:
    question = await db.prisma.question.find_unique(
        where={"id": question_id},
        include={"options": True}
    )
    return QuestionResponse.model_validate(question) if question else None

async def delete_question(question_id: str) -> QuestionResponse | None:
    deleted = await db.prisma.question.delete(
        where={"id": question_id}
    )
    return QuestionResponse.model_validate(deleted) if deleted else None
