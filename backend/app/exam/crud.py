from app.core.database import prisma
from .schema import ExamInfoCreate, QuestionCreate
from typing import List

async def create_exam_atomic(
    data: ExamInfoCreate,
    questions: List[QuestionCreate],
    teacher_id: str
):
    async with prisma.tx() as tx:
        # Create exam
        exam = await tx.exam.create(
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

        created_questions = []

        for q in questions:
            
            question = await tx.question.create(
                data={
                    "text": q.text,
                    "options": q.options,
                    "correctAnswer": q.correctAnswer,
                    "marks": q.marks,
                    "examId": exam.id,
                    "imageUrl": q.imageUrl,
                    "questionType": q.questionType,
                }
            )
            created_questions.append(question)

        return {
            "exam": exam,
            "questions": created_questions
        }