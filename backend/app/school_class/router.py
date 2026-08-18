import logging
from typing import Annotated  # noqa: I001

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore

from app.api.deps import get_current_user
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.models import Role
from app.principals.crud import get_principal_by_teacher_id
from app.students.crud import get_student_by_user_id, get_students_by_class_id
from app.students.schemas import StudentResponse
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

from .crud import (
    assign_student_to_class,
    assign_teacher_to_class,
    create_school_class,
    delete_school_class,
    get_class_exam_results,
    get_school_class_by_id,
    get_school_classes_by_school_id,
)
from .schemas import (
    AssignStudentRequest,
    AssignTeacherRequest,
    SchoolClassCreateRequest,
    SchoolClassResponse,
)

router = APIRouter(prefix="/api/v1/classes", tags=["classes"])
logger = logging.getLogger(__name__)


@router.post(
    "", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED
)
async def create_class(
    class_data: SchoolClassCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create a new school class (Principal and Admin only)."""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can create new classes. Teachers cannot create classes on their own.",
        )
    logger.debug(
        "Received class creation request: %s from user: %s", class_data, current_user.id
    )
    created_class = await create_school_class(class_data, current_user.id)
    if not created_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create classes for your own school.",
        )

    await record_audit_event(
        action=AuditAction.CLASS_CREATED,
        resource_type=AuditResourceType.SCHOOL_CLASS,
        resource_id=created_class.id,
        metadata={"name": created_class.name, "schoolId": created_class.schoolId},
    )

    return created_class


@router.get("/school/{school_id}", response_model=list[SchoolClassResponse])
async def get_classes_for_school(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get classes for a school without exposing join codes publicly."""
    if current_user.role == Role.STUDENT:
        student = await get_student_by_user_id(current_user.id)
        if not student or student.schoolId != school_id:
            raise HTTPException(
                status_code=403, detail="Access denied for this school."
            )
        classes = await get_school_classes_by_school_id(school_id)
        return [
            school_class
            for school_class in classes
            if school_class.id == student.classId
        ]

    if current_user.role == Role.PRINCIPAL:
        from app.school.crud import get_school_by_user_id

        school = await get_school_by_user_id(current_user.id)
        if not (school and school.id == school_id):
            teacher = await get_teacher_by_user_id(current_user.id)
            if not teacher or teacher.schoolId != school_id:
                raise HTTPException(
                    status_code=403, detail="Access denied for this school."
                )

    elif current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != school_id:
            raise HTTPException(
                status_code=403, detail="Access denied for this school."
            )

    return await get_school_classes_by_school_id(school_id)


async def _check_class_access(
    current_user: UserResponse, school_class: SchoolClassResponse
):
    if current_user.role == Role.ADMIN:
        return
    if current_user.role == Role.STUDENT:
        student = await get_student_by_user_id(current_user.id)
        if not student or student.classId != school_class.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own class.",
            )
        return
    if current_user.role == Role.TEACHER:
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You must be a teacher at this school.",
            )
        return
    if current_user.role == Role.PRINCIPAL:
        from app.school.crud import get_school_by_user_id

        school = await get_school_by_user_id(current_user.id)
        if school and school.id == school_class.schoolId:
            return
        teacher = await get_teacher_by_user_id(current_user.id)
        if teacher:
            if teacher.schoolId == school_class.schoolId:
                return
            principal = await get_principal_by_teacher_id(teacher.id)
            if principal and principal.schoolId == school_class.schoolId:
                return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You must be the principal of this school.",
        )


@router.get("/{class_id}", response_model=SchoolClassResponse)
async def get_class_by_id(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get a specific class by ID with RBAC stringency."""
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    await _check_class_access(current_user, school_class)
    return school_class


@router.get("/{class_id}/students", response_model=list[StudentResponse])
async def get_students_for_class(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get all students for a specific class with RBAC."""
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    await _check_class_access(current_user, school_class)
    return await get_students_by_class_id(class_id)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Delete a school class."""
    success = await delete_school_class(class_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Class not found or you do not have permission to delete it.",
        )
    await record_audit_event(
        action=AuditAction.CLASS_DELETED,
        resource_type=AuditResourceType.SCHOOL_CLASS,
        resource_id=class_id,
    )
    return None


@router.post("/{class_id}/assign-student", status_code=status.HTTP_200_OK)
async def assign_student_endpoint(
    class_id: str,
    payload: AssignStudentRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Assign or transfer an enrolled student directly to this class (Staff only)"""
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff can assign students to classes.",
        )

    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    if current_user.role in (Role.TEACHER, Role.PRINCIPAL):
        teacher = await get_teacher_by_user_id(current_user.id)
        if not teacher or teacher.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only assign students to classes in your own school.",
            )

    success = await assign_student_to_class(class_id, payload.studentId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign student to class. Verify student exists.",
        )

    await record_audit_event(
        action="STUDENT_CLASS_ASSIGNED",
        resource_type=AuditResourceType.SCHOOL_CLASS,
        resource_id=class_id,
        metadata={"studentId": payload.studentId},
    )
    return {"message": "Student successfully assigned to class"}


@router.post("/{class_id}/assign-teacher", status_code=status.HTTP_200_OK)
async def assign_teacher_endpoint(
    class_id: str,
    payload: AssignTeacherRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Principal directly assigns a teacher to teach a class"""
    if current_user.role not in (Role.PRINCIPAL, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only school principals or admins can assign teachers to classes.",
        )

    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    await _check_class_access(current_user, school_class)

    success = await assign_teacher_to_class(class_id, payload.teacherId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign teacher to class. Verify teacher exists.",
        )

    await record_audit_event(
        action=AuditAction.TEACHER_CLASS_ASSIGNED,
        resource_type=AuditResourceType.TEACHER_CLASS,
        resource_id=class_id,
        metadata={"teacherId": payload.teacherId},
    )
    return {"message": "Teacher successfully assigned to class"}


@router.get("/{class_id}/results")
async def get_class_results_endpoint(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get aggregated exam results, leaderboard, and student scores for a class."""
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    await _check_class_access(current_user, school_class)
    return await get_class_exam_results(class_id)
