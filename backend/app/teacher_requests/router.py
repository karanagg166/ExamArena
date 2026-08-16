from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_staff_teacher, get_current_user
from app.core.models import Role
from app.principals.crud import get_principal_by_teacher_id
from app.teacher_requests import crud
from app.teacher_requests.schemas import (
    TeacherAssignClassesRequest,
    TeacherAssignClassesResponse,
    TeacherClassJoinRequestCreate,
    TeacherClassJoinRequestDecision,
    TeacherClassJoinRequestResponse,
    TeacherSchoolJoinRequestCreate,
    TeacherSchoolJoinRequestDecision,
    TeacherSchoolJoinRequestResponse,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/teacher-requests", tags=["teacher-requests"])


# ─── TEACHER CLASS REQUESTS ───────────────────────────────────────────────────


@router.post(
    "",
    response_model=TeacherClassJoinRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_teacher_class_request(
    payload: TeacherClassJoinRequestCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Teacher requests to teach a class in their school"""
    teacher = await get_current_staff_teacher(current_user)
    try:
        return await crud.create_teacher_class_request(teacher.id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get(
    "/me",
    response_model=list[TeacherClassJoinRequestResponse],
)
async def list_my_teacher_class_requests(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Teacher views their own class join requests"""
    teacher = await get_current_staff_teacher(current_user)
    return await crud.get_teacher_requests_for_teacher(teacher.id)


@router.get(
    "/school/{school_id}",
    response_model=list[TeacherClassJoinRequestResponse],
)
async def list_school_teacher_requests(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    status_filter: str | None = None,
):
    """Principal lists teacher class join requests for their school"""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can view teacher join requests.",
        )

    if current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Principal staff profile not found.",
            )
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal or principal.schoolId != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this school.",
            )

    return await crud.get_teacher_requests_by_school(school_id, status_filter)


@router.patch(
    "/{request_id}",
    response_model=TeacherClassJoinRequestResponse,
)
async def decide_teacher_class_request(
    request_id: str,
    decision: TeacherClassJoinRequestDecision,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Principal approves or rejects a teacher class join request"""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can decide teacher join requests.",
        )

    try:
        return await crud.decide_teacher_class_request(
            request_id=request_id,
            decision_status=decision.status,
            decided_by_user_name=current_user.name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


# ─── TEACHER SCHOOL JOIN REQUESTS ─────────────────────────────────────────────


@router.post(
    "/school",
    response_model=TeacherSchoolJoinRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_teacher_school_request(
    payload: TeacherSchoolJoinRequestCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Teacher requests to join a school (requires Principal approval)"""
    if current_user.role != Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can submit school join requests.",
        )
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found. Please complete profile setup first.",
        )

    try:
        return await crud.create_teacher_school_request(teacher.id, payload.schoolId)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get(
    "/school/me",
    response_model=list[TeacherSchoolJoinRequestResponse],
)
async def list_my_teacher_school_requests(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Teacher views their own school join requests"""
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        return []
    return await crud.get_teacher_school_requests_for_teacher(teacher.id)


@router.get(
    "/school-requests/{school_id}",
    response_model=list[TeacherSchoolJoinRequestResponse],
)
async def list_school_teacher_join_requests(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    status_filter: str | None = None,
):
    """Principal lists teacher school join requests for their school"""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can view teacher join requests.",
        )

    if current_user.role == Role.PRINCIPAL:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Principal staff profile not found.",
            )
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal or principal.schoolId != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this school.",
            )

    return await crud.get_teacher_school_requests_for_school(school_id, status_filter)


@router.patch(
    "/school-requests/{request_id}",
    response_model=TeacherSchoolJoinRequestResponse,
)
async def decide_teacher_school_request(
    request_id: str,
    decision: TeacherSchoolJoinRequestDecision,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Principal approves or rejects a teacher school join request"""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can decide school join requests.",
        )

    try:
        return await crud.decide_teacher_school_request(
            request_id=request_id,
            decision_status=decision.status,
            decided_by_user_name=current_user.name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


# ─── MULTI-CLASS ASSIGNMENT BY PRINCIPAL ──────────────────────────────────────


@router.post(
    "/assign-classes",
    response_model=TeacherAssignClassesResponse,
)
async def assign_classes_to_teacher(
    payload: TeacherAssignClassesRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Principal assigns multiple classes to a teacher in their school"""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can assign classes to teachers.",
        )

    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Principal staff profile not found.",
        )
    principal = await get_principal_by_teacher_id(teacher.id)
    if not principal or not principal.schoolId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Principal does not have an active school.",
        )

    try:
        return await crud.assign_multiple_classes_to_teacher(
            school_id=principal.schoolId,
            teacher_id=payload.teacherId,
            class_ids=payload.classIds,
            subject=payload.subject,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
