
from fastapi import APIRouter, HTTPException
from typing import List
from .schema import ExamAtomicCreate
from .crud import create_exam_atomic
from app.api.deps import get_current_user
from app.teachers.crud import get_teacher_by_user_id
from fastapi import Depends

router = APIRouter(prefix="/api/v1", tags=["exam"])

@router.post("/createExamAtomic")
async def create_exam_atomic_endpoint(
    data: ExamAtomicCreate,
    current_user=Depends(get_current_user)
):
    try:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(status_code=400, detail="Teacher profile not found")
        exam, questions = await create_exam_atomic(data.examInfo, data.questions, teacher.id)
        return {"success": True, "exam": exam, "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))