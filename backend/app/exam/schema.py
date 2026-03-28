from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ExamInfoCreate(BaseModel):
    name: str
    description: str
    date: datetime
    duration: int
    maxMarks: int
    type: str  # Should match ExamType enum

class QuestionCreate(BaseModel):
    text: str
    options: List[str]
    correctAnswer: Optional[str]
    marks: int
    imageUrl: Optional[str] = None
    questionType: Optional[str] = "MULTIPLE_CHOICE"
    
class ExamAtomicCreate(BaseModel):
    examInfo: ExamInfoCreate
    questions: List[QuestionCreate]

