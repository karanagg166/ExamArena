from app.core.database import prisma
from .schema import ExamInfoCreate, QuestionCreate
from typing import List

async def create_exam_info(data: ExamInfoCreate, teacher_id: str):
    exam = await prisma.exam.create(
        data={
            "name": data.name,
            "description": data.description,
            "date": data.date,
            "duration": data.duration,
            "maxMarks": data.maxMarks,
            "type": data.type,
            "teacherId": teacher_id,
        }
    )
    return exam

async def create_exam_questions(questions: List[QuestionCreate]):
    created = []
    for q in questions:
        question = await prisma.question.create(
            data={
                "text": q.text,
                "options": q.options,
                "correctAnswer": q.correctAnswer,
                "marks": q.marks,
                "examId": q.examId,
                "imageUrl": q.imageUrl,
                "questionType": q.questionType,
            }
        )
        created.append(question)
    return created
