"""FastAPI router for student answer grading and AI-assisted evaluation."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.grading.service import (
    AIGradingProviderError,
    AIGradingService,
    AIGradingValidationError,
    GradingContextMissingError,
    GradingEligibilityError,
)
from app.api.deps import get_current_user
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.database import get_db
from app.core.models import QuestionType
from app.grading import crud
from app.grading.permissions import require_answer_grading_access
from app.grading.schemas import (
    AIGradingProposalResponse,
    RubricGradeResponse,
    TeacherGradeResponse,
    TeacherGradeUpdateRequest,
    TeacherStudentAnswerDetailResponse,
)
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/student-answers", tags=["grading"])


@router.post(
    "/{answer_id}/ai-grade",
    response_model=AIGradingProposalResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_ai_grading_proposal(
    answer_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Generates an AI-assisted grading proposal for a subjective student answer.

    Enforces teacher authorization and validates invariants.
    AI proposal is saved as draft and DOES NOT finalize student marks.
    """
    answer, _ = await require_answer_grading_access(current_user, answer_id, session)

    question = answer.question
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated question not found for this answer",
        )

    # Validate subjective eligibility
    if answer.questionType not in (QuestionType.SHORT_ANSWER, QuestionType.ESSAY):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI grading is only supported for SHORT_ANSWER and ESSAY questions, received: {answer.questionType.value}",
        )

    exam = answer.studentExam.exam if answer.studentExam else None
    ai_service = AIGradingService()

    try:
        proposal = await ai_service.grade_subjective_answer(
            question_text=question.text,
            question_type=answer.questionType,
            max_marks=float(question.marks),
            student_answer=answer.textAnswer,
            reference_answer=question.referenceAnswer,
            grading_rubric=question.gradingRubric,
            explanation=question.explanation,
            subject=exam.subject.value if (exam and exam.subject) else None,
            exam_title=exam.name if exam else None,
        )
    except GradingEligibilityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except GradingContextMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AIGradingValidationError as exc:
        logger.warning("AI grading proposal rejected by invariant check: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"AI grading result failed validation: {exc}",
        ) from exc
    except AIGradingProviderError as exc:
        logger.error("AI grading provider error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI grading service is currently unavailable. Please grade manually.",
        ) from exc

    saved_answer = await crud.save_ai_grading_proposal(answer, proposal, session)

    await record_audit_event(
        action=AuditAction.AI_GRADE_PROPOSED,
        resource_type=AuditResourceType.GRADING,
        resource_id=saved_answer.id,
        metadata={
            "suggestedMarks": proposal.suggested_marks,
            "maxMarks": proposal.max_marks,
            "confidence": proposal.confidence.value,
        },
        session=session,
    )

    breakdown_responses = [
        RubricGradeResponse(
            criterion=item.criterion,
            maxMarks=item.max_marks,
            awardedMarks=item.awarded_marks,
            justification=item.justification,
        )
        for item in proposal.rubric_breakdown
    ]

    return AIGradingProposalResponse(
        answerId=saved_answer.id,
        suggestedMarks=saved_answer.aiSuggestedMarks or 0.0,
        maxMarks=float(question.marks),
        rubricBreakdown=breakdown_responses,
        feedback=saved_answer.aiFeedback or "",
        confidence=saved_answer.aiConfidence or "HIGH",
        warnings=saved_answer.aiWarnings or [],
    )


@router.post(
    "/{answer_id}/grade/accept-ai",
    response_model=TeacherGradeResponse,
    status_code=status.HTTP_200_OK,
)
async def accept_ai_grade(
    answer_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Adopts the existing AI grading suggestion as the final teacher-approved mark and feedback."""
    answer, _ = await require_answer_grading_access(current_user, answer_id, session)

    if answer.aiSuggestedMarks is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI grading proposal available to accept",
        )

    try:
        updated = await crud.accept_ai_grading_proposal(
            answer=answer,
            teacher_user_id=current_user.id,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        action=AuditAction.AI_GRADE_ACCEPTED,
        resource_type=AuditResourceType.GRADING,
        resource_id=updated.id,
        metadata={
            "marksAwarded": updated.marksAwarded,
            "gradingStatus": updated.gradingStatus.value,
        },
        session=session,
    )

    return TeacherGradeResponse(
        answerId=updated.id,
        studentExamId=updated.studentExamId,
        questionId=updated.questionId,
        marksAwarded=float(updated.marksAwarded or 0.0),
        maxMarks=float(updated.question.marks if updated.question else 0.0),
        feedback=updated.feedback,
        gradingStatus=updated.gradingStatus.value,
        gradedBy=updated.gradedBy,
        gradedAt=updated.gradedAt,
        isCorrect=updated.isCorrect.value if updated.isCorrect else None,
    )


@router.patch(
    "/{answer_id}/grade",
    response_model=TeacherGradeResponse,
    status_code=status.HTTP_200_OK,
)
async def modify_student_grade(
    answer_id: str,
    payload: TeacherGradeUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Allows the teacher to manually grade or override AI marks and feedback, finalizing the grade."""
    answer, _ = await require_answer_grading_access(current_user, answer_id, session)

    max_marks = float(answer.question.marks if answer.question else 0.0)
    if payload.marks < 0 or payload.marks > max_marks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Marks must be between 0 and {max_marks}",
        )

    try:
        updated = await crud.apply_teacher_grade_override(
            answer=answer,
            marks=payload.marks,
            feedback=payload.feedback,
            teacher_user_id=current_user.id,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        action=AuditAction.MANUAL_GRADE_UPDATED,
        resource_type=AuditResourceType.GRADING,
        resource_id=updated.id,
        metadata={
            "marksAwarded": updated.marksAwarded,
            "feedback": updated.feedback,
        },
        session=session,
    )

    return TeacherGradeResponse(
        answerId=updated.id,
        studentExamId=updated.studentExamId,
        questionId=updated.questionId,
        marksAwarded=float(updated.marksAwarded or 0.0),
        maxMarks=max_marks,
        feedback=updated.feedback,
        gradingStatus=updated.gradingStatus.value,
        gradedBy=updated.gradedBy,
        gradedAt=updated.gradedAt,
        isCorrect=updated.isCorrect.value if updated.isCorrect else None,
    )


@router.post(
    "/{answer_id}/grade/reject-ai",
    status_code=status.HTTP_200_OK,
)
async def reject_ai_grade(
    answer_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Discards/rejects the AI proposal, allowing teacher to evaluate manually from scratch."""
    answer, _ = await require_answer_grading_access(current_user, answer_id, session)

    updated = await crud.reject_ai_grading_proposal(answer, session)

    await record_audit_event(
        action=AuditAction.AI_GRADE_REJECTED,
        resource_type=AuditResourceType.GRADING,
        resource_id=updated.id,
        session=session,
    )

    return {
        "answerId": updated.id,
        "status": "REJECTED",
        "message": "AI grading proposal rejected. Answer is ready for manual grading.",
    }


@router.get(
    "/{answer_id}",
    response_model=TeacherStudentAnswerDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_answer_details_for_grading(
    answer_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieves full student answer, question details, reference solutions, AI proposal, and teacher grade."""
    answer, _ = await require_answer_grading_access(current_user, answer_id, session)
    question = answer.question

    ai_proposal = None
    if answer.aiSuggestedMarks is not None:
        raw_breakdown = answer.aiGradingBreakdown or []
        breakdown_objs = [
            RubricGradeResponse(
                criterion=item.get("criterion", ""),
                maxMarks=float(item.get("max_marks", item.get("maxMarks", 0.0))),
                awardedMarks=float(item.get("awarded_marks", item.get("awardedMarks", 0.0))),
                justification=item.get("justification", ""),
            )
            for item in raw_breakdown
        ]
        ai_proposal = AIGradingProposalResponse(
            answerId=answer.id,
            suggestedMarks=float(answer.aiSuggestedMarks),
            maxMarks=float(question.marks if question else 0.0),
            rubricBreakdown=breakdown_objs,
            feedback=answer.aiFeedback or "",
            confidence=answer.aiConfidence or "HIGH",
            warnings=answer.aiWarnings or [],
        )

    final_grade = None
    if answer.marksAwarded is not None:
        final_grade = TeacherGradeResponse(
            answerId=answer.id,
            studentExamId=answer.studentExamId,
            questionId=answer.questionId,
            marksAwarded=float(answer.marksAwarded),
            maxMarks=float(question.marks if question else 0.0),
            feedback=answer.feedback,
            gradingStatus=answer.gradingStatus.value,
            gradedBy=answer.gradedBy,
            gradedAt=answer.gradedAt,
            isCorrect=answer.isCorrect.value if answer.isCorrect else None,
        )

    return TeacherStudentAnswerDetailResponse(
        id=answer.id,
        studentExamId=answer.studentExamId,
        questionId=answer.questionId,
        questionType=answer.questionType.value,
        questionNumber=question.questionNumber if question else 1,
        questionText=question.text if question else "",
        maxMarks=float(question.marks if question else 0.0),
        studentAnswer=answer.textAnswer,
        referenceAnswer=question.referenceAnswer if question else None,
        gradingRubric=question.gradingRubric if question else None,
        explanation=question.explanation if question else None,
        aiProposal=ai_proposal,
        finalGrade=final_grade,
    )
