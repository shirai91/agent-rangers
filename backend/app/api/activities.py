"""API endpoints for activity operations."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.activity_service import ActivityService
from app.schemas.activity import (
    TaskActivityResponse,
    TaskActivityListResponse,
    BoardActivityResponse,
)

router = APIRouter()


@router.get(
    "/tasks/{task_id}/activities",
    response_model=TaskActivityListResponse,
)
async def get_task_activities(
    task_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get activities for a specific task with pagination.

    Args:
        task_id: Task UUID
        page: Page number (1-based)
        page_size: Number of items per page (max 100)

    Returns:
        Paginated list of activities
    """
    activities, total = await ActivityService.get_task_activities(
        db, task_id, page, page_size
    )

    return TaskActivityListResponse(
        items=[_activity_to_response(a) for a in activities],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/boards/{board_id}/activities",
    response_model=BoardActivityResponse,
)
async def get_board_activities(
    board_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get activities for a specific board with pagination.

    Args:
        board_id: Board UUID
        page: Page number (1-based)
        page_size: Number of items per page (max 100)

    Returns:
        Paginated list of activities for the board
    """
    activities, total = await ActivityService.get_board_activities(
        db, board_id, page, page_size
    )

    return BoardActivityResponse(
        activities=[_activity_to_response(a) for a in activities],
        total=total,
    )


@router.get(
    "/boards/{board_id}/activities/recent",
)
async def get_recent_board_activities(
    board_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent activities for a board.

    Args:
        board_id: Board UUID
        limit: Maximum number of activities to return

    Returns:
        List of recent activities
    """
    activities = await ActivityService.get_recent_board_activities(db, board_id, limit)

    return [_activity_to_response(a) for a in activities]


def _activity_to_response(activity) -> TaskActivityResponse:
    """Convert a TaskActivity model to response schema."""
    return TaskActivityResponse(
        id=activity.id,
        task_id=activity.task_id,
        board_id=activity.board_id,
        activity_type=activity.activity_type,
        actor=activity.actor,
        from_column_id=activity.from_column_id,
        to_column_id=activity.to_column_id,
        old_value=activity.old_value,
        new_value=activity.new_value,
        activity_metadata=activity.activity_metadata,
        created_at=activity.created_at,
        from_column_name=getattr(activity, "_from_column_name", None),
        to_column_name=getattr(activity, "_to_column_name", None),
        task_title=activity.task.title if hasattr(activity, "task") and activity.task else None,
    )
