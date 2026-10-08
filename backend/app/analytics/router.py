"""FastAPI router for Teacher Results Analytics."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.constants import DEFAULT_PAGE_SIZE
from app.analytics.schemas import (
    AnalyticsSortBy,
    ClassLeaderboardResponse,
    ClassResultsResponse,
    ExamAnalyticsDetailResponse,
    PerformanceBracket,
    SortOrder,
    StudentResultsResponse,
    TeacherResultsOverviewResponse,
)
from app.analytics.service import AnalyticsService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.models import Role, Subject
from app.core.rbac import enforce_rbac_permission
from app.users.schemas import UserResponse

logger = logging.getLogger("exam_arena.analytics.router")

router = APIRouter(tags=["analytics"])


@router.get(
    "/api/v1/teacher/results/overview",
    response_model=TeacherResultsOverviewResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/api/v1/teachers/results/overview",
    response_model=TeacherResultsOverviewResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.get(
    "/api/v1/analytics/overview",
    response_model=TeacherResultsOverviewResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_teacher_results_overview_endpoint(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieves teacher results analytics overview metrics (total exams, attempts, pass/graded stats)."""
    enforce_rbac_permission(current_user.role, "analytics", "read")
    return await AnalyticsService.get_teacher_overview(
        current_user=current_user,
        session=session,
    )


@router.get(
    "/api/v1/classes/{class_id}/analytics",
    response_model=ClassResultsResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/api/v1/analytics/classes/{class_id}/results",
    response_model=ClassResultsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_class_analytics_endpoint(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    subject: Subject | None = None,
    date_from: Annotated[datetime | None, Query(alias="dateFrom")] = None,
    date_to: Annotated[datetime | None, Query(alias="dateTo")] = None,
):
    """Retrieves class-level performance summary and exam breakdown."""
    enforce_rbac_permission(current_user.role, "analytics", "read")
    return await AnalyticsService.get_class_analytics(
        class_id=class_id,
        current_user=current_user,
        session=session,
        subject=subject,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/api/v1/classes/{class_id}/leaderboard",
    response_model=ClassLeaderboardResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/api/v1/analytics/classes/{class_id}/leaderboard",
    response_model=ClassLeaderboardResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_class_leaderboard_endpoint(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = None,
    min_percentage: Annotated[float | None, Query(alias="minPercentage")] = None,
    max_percentage: Annotated[float | None, Query(alias="maxPercentage")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Retrieves normalized multi-exam leaderboard ranking across finalized exams for a class."""
    enforce_rbac_permission(current_user.role, "analytics", "read")
    return await AnalyticsService.get_class_leaderboard(
        class_id=class_id,
        current_user=current_user,
        session=session,
        search=search,
        min_percentage=min_percentage,
        max_percentage=max_percentage,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/v1/students/{student_id}/results",
    response_model=StudentResultsResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/api/v1/analytics/students/{student_id}/results",
    response_model=StudentResultsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_student_results_endpoint(
    student_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    subject: Subject | None = None,
    date_from: Annotated[datetime | None, Query(alias="dateFrom")] = None,
    date_to: Annotated[datetime | None, Query(alias="dateTo")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Retrieves student exam history and performance summary for authorized staff or self."""
    action = "read_own" if current_user.role == Role.STUDENT else "read"
    enforce_rbac_permission(current_user.role, "results", action)
    return await AnalyticsService.get_student_results_for_teacher(
        student_id=student_id,
        current_user=current_user,
        session=session,
        subject=subject,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/v1/exams/{exam_id}/analytics",
    response_model=ExamAnalyticsDetailResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/api/v1/analytics/exams/{exam_id}",
    response_model=ExamAnalyticsDetailResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_exam_analytics_endpoint(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = None,
    bracket: PerformanceBracket = PerformanceBracket.ALL,
    min_percentage: Annotated[float | None, Query(alias="minPercentage")] = None,
    max_percentage: Annotated[float | None, Query(alias="maxPercentage")] = None,
    sort_by: Annotated[AnalyticsSortBy, Query(alias="sortBy")] = AnalyticsSortBy.RANK,
    sort_order: Annotated[SortOrder, Query(alias="sortOrder")] = SortOrder.ASC,
    limit: Annotated[int, Query(ge=1, le=100)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Retrieves exam-level analytics, subjective grading workload, and filtered scoreboard."""
    enforce_rbac_permission(current_user.role, "analytics", "read")
    return await AnalyticsService.get_exam_analytics(
        exam_id=exam_id,
        current_user=current_user,
        session=session,
        search=search,
        bracket=bracket,
        min_percentage=min_percentage,
        max_percentage=max_percentage,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
