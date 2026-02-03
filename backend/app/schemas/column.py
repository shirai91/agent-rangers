"""Pydantic schemas for Column model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ColumnBase(BaseModel):
    """Base schema for Column with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Column name")
    color: Optional[str] = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code (e.g., #6366f1)",
    )
    wip_limit: Optional[int] = Field(
        None,
        ge=0,
        description="Work-in-progress limit",
    )


class ColumnCreate(ColumnBase):
    """Schema for creating a new column."""

    order: Optional[float] = Field(
        None,
        description="Position order (auto-calculated if not provided)",
    )


class ColumnUpdate(BaseModel):
    """Schema for updating a column (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    order: Optional[float] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    wip_limit: Optional[int] = Field(None, ge=0)


class ColumnResponse(ColumnBase):
    """Schema for column response with all fields."""

    id: UUID
    board_id: UUID
    order: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
