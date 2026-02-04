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
    triggers_agents: bool = Field(
        False,
        description="Whether moving a task to this column triggers AI agents",
    )
    is_start_column: bool = Field(
        False,
        description="Whether this is a starting column for new tasks",
    )
    is_end_column: bool = Field(
        False,
        description="Whether this is an ending/done column",
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
    triggers_agents: Optional[bool] = None
    agent_workflow_type: Optional[str] = None
    is_start_column: Optional[bool] = None
    is_end_column: Optional[bool] = None


class ColumnResponse(BaseModel):
    """Schema for column response with all fields."""

    id: UUID
    board_id: UUID
    name: str
    order: float
    color: Optional[str] = None
    wip_limit: Optional[int] = None
    triggers_agents: bool
    agent_workflow_type: Optional[str] = None
    is_start_column: bool
    is_end_column: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
