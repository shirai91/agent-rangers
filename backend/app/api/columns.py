"""API endpoints for column operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.board_service import BoardService
from app.schemas.column import ColumnUpdate, ColumnResponse

router = APIRouter()


@router.put("/{column_id}", response_model=ColumnResponse)
async def update_column(
    column_id: UUID,
    column_data: ColumnUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a column.

    Args:
        column_id: Column UUID
        column_data: Column update data

    Returns:
        Updated column

    Raises:
        HTTPException: 404 if column not found
    """
    column = await BoardService.update_column(db, column_id, column_data)
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column {column_id} not found",
        )
    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a column.

    Args:
        column_id: Column UUID

    Raises:
        HTTPException: 404 if column not found
    """
    deleted = await BoardService.delete_column(db, column_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column {column_id} not found",
        )
