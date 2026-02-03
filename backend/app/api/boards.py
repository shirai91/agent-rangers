"""API endpoints for board operations."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.board_service import BoardService
from app.schemas.board import (
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    BoardListResponse,
)
from app.schemas.column import ColumnCreate, ColumnResponse
from app.schemas.task import TaskCreate, TaskResponse

router = APIRouter()


@router.get("", response_model=List[BoardListResponse])
async def get_boards(db: AsyncSession = Depends(get_db)):
    """
    Get all boards (without columns for performance).

    Returns:
        List of boards
    """
    boards = await BoardService.get_boards(db)
    return boards


@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_data: BoardCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new board.

    Args:
        board_data: Board creation data

    Returns:
        Created board with columns
    """
    board = await BoardService.create_board(db, board_data)
    return board


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a board by ID with all columns.

    Args:
        board_id: Board UUID

    Returns:
        Board with columns

    Raises:
        HTTPException: 404 if board not found
    """
    board = await BoardService.get_board(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board {board_id} not found",
        )
    return board


@router.put("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: UUID,
    board_data: BoardUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a board.

    Args:
        board_id: Board UUID
        board_data: Board update data

    Returns:
        Updated board

    Raises:
        HTTPException: 404 if board not found
    """
    board = await BoardService.update_board(db, board_id, board_data)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board {board_id} not found",
        )
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a board.

    Args:
        board_id: Board UUID

    Raises:
        HTTPException: 404 if board not found
    """
    deleted = await BoardService.delete_board(db, board_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board {board_id} not found",
        )


@router.get("/{board_id}/columns", response_model=List[ColumnResponse])
async def get_board_columns(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all columns for a board.

    Args:
        board_id: Board UUID

    Returns:
        List of columns ordered by position
    """
    columns = await BoardService.get_columns(db, board_id)
    return columns


@router.post(
    "/{board_id}/columns",
    response_model=ColumnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_column(
    board_id: UUID,
    column_data: ColumnCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new column for a board.

    Args:
        board_id: Board UUID
        column_data: Column creation data

    Returns:
        Created column

    Raises:
        HTTPException: 404 if board not found
    """
    column = await BoardService.create_column(db, board_id, column_data)
    return column


@router.get("/{board_id}/tasks", response_model=List[TaskResponse])
async def get_board_tasks(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all tasks for a board.

    Args:
        board_id: Board UUID

    Returns:
        List of tasks
    """
    tasks = await BoardService.get_tasks(db, board_id)
    return tasks


@router.post(
    "/{board_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    board_id: UUID,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new task for a board.

    Args:
        board_id: Board UUID
        task_data: Task creation data

    Returns:
        Created task

    Raises:
        HTTPException: 404 if board or column not found
    """
    task = await BoardService.create_task(db, board_id, task_data)
    return task
