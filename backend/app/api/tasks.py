"""API endpoints for task operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.board_service import BoardService
from app.schemas.task import TaskUpdate, TaskMove, TaskResponse

router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a task by ID.

    Args:
        task_id: Task UUID

    Returns:
        Task details

    Raises:
        HTTPException: 404 if task not found
    """
    task = await BoardService.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a task with optimistic locking.

    Args:
        task_id: Task UUID
        task_data: Task update data (including version for locking)

    Returns:
        Updated task with new version

    Raises:
        HTTPException: 404 if task not found, 409 if version conflict
    """
    task = await BoardService.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


@router.put("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: UUID,
    move_data: TaskMove,
    db: AsyncSession = Depends(get_db),
):
    """
    Move a task to a different column with optimistic locking.

    Args:
        task_id: Task UUID
        move_data: Move operation data (column_id, order, version)

    Returns:
        Updated task with new version

    Raises:
        HTTPException: 404 if task or column not found, 409 if version conflict
    """
    task = await BoardService.move_task(db, task_id, move_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a task.

    Args:
        task_id: Task UUID

    Raises:
        HTTPException: 404 if task not found
    """
    deleted = await BoardService.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
