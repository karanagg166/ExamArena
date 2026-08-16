from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.core.models import JoinRequestStatus, Role
from app.join_requests.crud import (
    create_or_reopen_join_request,
    decide_join_request,
    get_class_by_join_code,
    get_join_request_by_id,
    get_join_requests_for_class,
    get_join_requests_for_school,
    get_join_requests_for_user,
)
from app.join_requests.schemas import (
    JoinByCodeRequest,
    JoinRequestDecision,
    JoinRequestResponse,
)
from app.principals.crud import get_principal_by_teacher_id
from app.school_class.crud import get_school_class_by_id
from app.students.crud import get_student_by_user_id
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/join-requests", tags=["join-requests"])


async def _get_authorized_teacher_id(current_user: UserResponse, school_id: str) -> str:
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=403, detail="Only staff can manage join requests."
        )

    teacher = await get_teacher_by_user_id(current_user.id)
    if current_user.role == Role.ADMIN:
        return teacher.id if teacher else current_user.id

    if teacher:
        if teacher.schoolId == school_id:
            return teacher.id
        if any(
            tc.schoolClass and tc.schoolClass.schoolId == school_id
            for tc in getattr(teacher, "teaches", [])
        ):
            return teacher.id

    if current_user.role == Role.PRINCIPAL:
        from app.school.crud import get_school_by_user_id

        user_school = await get_school_by_user_id(current_user.id)
        if user_school and user_school.id == school_id:
            return teacher.id if teacher else current_user.id

        if teacher:
            principal = await get_principal_by_teacher_id(teacher.id)
            if principal and principal.schoolId == school_id:
                return teacher.id

    raise HTTPException(status_code=403, detail="Access denied for this school.")


@router.post(
    "/join-by-code",
    response_model=JoinRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_by_code(
    payload: JoinByCodeRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can join a class.")
    if await get_student_by_user_id(current_user.id):
        raise HTTPException(status_code=409, detail="Student profile already exists.")

    school_class = await get_class_by_join_code(payload.joinCode)
    if not school_class:
        raise HTTPException(status_code=404, detail="Invalid or expired join code.")
    try:
        return await create_or_reopen_join_request(current_user.id, school_class)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/me", response_model=list[JoinRequestResponse])
async def get_my_join_requests(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if current_user.role != Role.STUDENT:
        raise HTTPException(
            status_code=403, detail="Only students can view these requests."
        )
    return await get_join_requests_for_user(current_user.id)


@router.get("/school/{school_id}", response_model=list[JoinRequestResponse])
async def get_school_join_requests(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    request_status: Annotated[JoinRequestStatus | None, Query(alias="status")] = None,
):
    """Get all student class join requests across all classes of a school for Principal/Teacher review."""
    await _get_authorized_teacher_id(current_user, school_id)
    return await get_join_requests_for_school(school_id, request_status)


@router.get("/class/{class_id}", response_model=list[JoinRequestResponse])
async def get_class_join_requests(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    request_status: Annotated[
        JoinRequestStatus, Query(alias="status")
    ] = JoinRequestStatus.PENDING,
):
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    await _get_authorized_teacher_id(current_user, school_class.schoolId)
    return await get_join_requests_for_class(class_id, request_status)


@router.patch("/{request_id}", response_model=JoinRequestResponse)
async def decide_request(
    request_id: str,
    decision: JoinRequestDecision,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    request = await get_join_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Join request not found")

    teacher_id = await _get_authorized_teacher_id(
        current_user, request.schoolClass.schoolId
    )
    try:
        updated = await decide_join_request(
            request_id=request_id,
            decision=JoinRequestStatus(decision.status),
            decided_by_user_id=teacher_id,
            roll_no=decision.rollNo,
            auto_roll_no=decision.autoRollNo,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(
            status_code=409, detail="Only pending requests can be decided."
        )
    return updated
