"""API endpoints for task operations."""

import asyncio
import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.board_service import BoardService
from app.services.file_storage import file_storage
from app.services.task_evaluator import task_evaluator
from app.schemas.task import TaskUpdate, TaskMove, TaskResponse

logger = logging.getLogger(__name__)

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
    # Check if title or description is being updated (triggers re-evaluation)
    should_evaluate = task_data.title is not None or task_data.description is not None

    task = await BoardService.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Trigger background evaluation if title or description changed
    if should_evaluate:
        asyncio.create_task(
            _run_task_evaluation(
                board_id=str(task.board_id),
                task_id=str(task.id),
                task_title=task.title,
                task_description=task.description or "",
            )
        )

    return task


async def _run_task_evaluation(
    board_id: str,
    task_id: str,
    task_title: str,
    task_description: str,
) -> None:
    """
    Run task evaluation in the background.

    This is a fire-and-forget operation that evaluates a task and stores
    the result in info.json.

    Args:
        board_id: The UUID of the board as a string.
        task_id: The UUID of the task as a string.
        task_title: The title of the task.
        task_description: The description of the task.
    """
    try:
        await task_evaluator.evaluate_task(
            board_id,
            task_id,
            task_title,
            task_description,
        )
    except Exception:
        logger.exception(f"Failed to evaluate task {task_id}")


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


class RepositoryMatch(BaseModel):
    """Schema for repository match in evaluation result."""

    path: str
    name: str
    confidence: float
    reasoning: str


class EvaluationContext(BaseModel):
    """Schema for evaluation context."""

    relevant_files: list[str]
    technologies: list[str]


class TaskEvaluationResponse(BaseModel):
    """Schema for task evaluation response."""

    task_id: str
    evaluated_at: str
    repository: Optional[RepositoryMatch] = None
    context: EvaluationContext


@router.get("/{task_id}/evaluation", response_model=TaskEvaluationResponse)
async def get_task_evaluation(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the evaluation result for a task.

    Retrieves the info.json file containing the LLM-generated evaluation
    that matches the task to a repository.

    Args:
        task_id: Task UUID

    Returns:
        Evaluation result with repository match and context

    Raises:
        HTTPException: 404 if task not found or evaluation not available
    """
    # First verify the task exists and get board_id
    task = await BoardService.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Load the evaluation result from info.json
    board_id = str(task.board_id)
    content = file_storage.load_output(board_id, str(task_id), "info.json")

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation not available for task {task_id}",
        )

    try:
        result = json.loads(content)
        return TaskEvaluationResponse(**result)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse evaluation for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse evaluation result",
        )


@router.post("/{task_id}/evaluation", response_model=TaskEvaluationResponse)
async def trigger_task_evaluation(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a new evaluation for a task.

    Forces re-evaluation of the task using the LLM to match it to a repository.

    Args:
        task_id: Task UUID

    Returns:
        Evaluation result with repository match and context

    Raises:
        HTTPException: 404 if task not found
    """
    # First verify the task exists
    task = await BoardService.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Run evaluation
    result = await task_evaluator.evaluate_task(
        str(task.board_id),
        str(task_id),
        task.title,
        task.description or "",
    )

    return TaskEvaluationResponse(**result)
