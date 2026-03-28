
from fastapi import APIRouter, HTTPException
from typing import List
from .schema import ExamInfoCreate, QuestionCreate
from .crud import create_exam_info as create_exam_info_crud, create_exam_questions as create_exam_questions_crud
from app.api.deps import get_current_user
from app.teachers.crud import get_teacher_by_user_id
from fastapi import Depends

router = APIRouter(prefix="/api/v1", tags=["exam"])

@router.post("/createExamInfo")
async def create_exam_info(
    data: ExamInfoCreate,
    current_user=Depends(get_current_user)
):
    try:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(status_code=400, detail="Teacher profile not found")
        exam = await create_exam_info_crud(data, teacher.id)
        return {"success": True, "exam": exam, "examId": exam.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/createExamQuestions")
async def create_exam_questions(questions: List[QuestionCreate]):
    try:
        questions = await create_exam_questions_crud(questions)
        return {"success": True, "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
