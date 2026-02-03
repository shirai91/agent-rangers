"""Pydantic schemas for TaskActivity model."""

from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


ActivityType = Literal[
    "created",
    "updated",
    "moved",
    "deleted",
    "assigned",
    "unassigned",
    "priority_changed",
    "status_changed",
    "comment",
]


class TaskActivityBase(BaseModel):
    """Base schema for TaskActivity with common fields."""

    activity_type: str = Field(..., max_length=50, description="Type of activity")
    actor: str = Field("system", max_length=255, description="Who performed the action")
    from_column_id: Optional[UUID] = Field(None, description="Source column for move activities")
    to_column_id: Optional[UUID] = Field(None, description="Target column for move activities")
    old_value: Optional[dict] = Field(None, description="Previous value before change")
    new_value: Optional[dict] = Field(None, description="New value after change")
    activity_metadata: dict = Field(default_factory=dict, description="Additional activity metadata")


class TaskActivityCreate(TaskActivityBase):
    """Schema for creating a new task activity."""

    task_id: UUID = Field(..., description="Task ID")
    board_id: UUID = Field(..., description="Board ID")


class TaskActivityResponse(BaseModel):
    """Schema for task activity response with all fields."""

    id: UUID
    task_id: UUID
    board_id: UUID
    activity_type: str
    actor: str
    from_column_id: Optional[UUID] = None
    to_column_id: Optional[UUID] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    activity_metadata: dict = Field(default_factory=dict, alias="activity_metadata")
    created_at: datetime

    # Populated from relationships for display
    from_column_name: Optional[str] = None
    to_column_name: Optional[str] = None
    task_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TaskActivityListResponse(BaseModel):
    """Schema for paginated task activity list response."""

    items: List[TaskActivityResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BoardActivityResponse(BaseModel):
    """Schema for board-level activity feed."""

    activities: List[TaskActivityResponse]
    total: int
