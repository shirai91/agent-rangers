"""Pydantic schemas for Task model."""

from datetime import datetime
from typing import Optional, List, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TaskBase(BaseModel):
    """Base schema for Task with common fields."""

    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: int = Field(
        default=0,
        ge=0,
        le=4,
        description="Priority: 0=none, 1=low, 2=medium, 3=high, 4=critical",
    )
    labels: List[str] = Field(default_factory=list, description="Task labels")

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Union[int, str]) -> int:
        """
        Validate and convert priority from string or integer to integer.

        Accepts:
        - Integer values: 0-4
        - String values: 'none', 'low', 'medium', 'high', 'critical'

        Returns integer representation (0-4).
        """
        # Priority mapping
        priority_map = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }

        # If already an integer, validate range
        if isinstance(v, int):
            if v < 0 or v > 4:
                raise ValueError("Priority must be between 0 and 4")
            return v

        # If string, convert to integer
        if isinstance(v, str):
            normalized = v.lower().strip()
            if normalized not in priority_map:
                raise ValueError(
                    f"Invalid priority string: '{v}'. "
                    f"Valid values: {', '.join(priority_map.keys())}"
                )
            return priority_map[normalized]

        # Invalid type
        raise ValueError(f"Priority must be an integer (0-4) or string, got {type(v)}")

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: List[str]) -> List[str]:
        """Validate labels are strings and not too long."""
        if not isinstance(v, list):
            raise ValueError("Labels must be a list")
        for label in v:
            if not isinstance(label, str):
                raise ValueError("Each label must be a string")
            if len(label) > 50:
                raise ValueError("Label too long (max 50 characters)")
        return v


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    column_id: Optional[UUID] = Field(None, description="Column ID (optional)")
    order: Optional[float] = Field(
        None,
        description="Position order (auto-calculated if not provided)",
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=4)
    labels: Optional[List[str]] = None
    column_id: Optional[UUID] = None
    order: Optional[float] = None
    version: Optional[int] = Field(
        None,
        description="Current version for optimistic locking",
    )

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Union[int, str, None]) -> Optional[int]:
        """
        Validate and convert priority from string or integer to integer.

        Accepts:
        - Integer values: 0-4
        - String values: 'none', 'low', 'medium', 'high', 'critical'
        - None (for optional updates)

        Returns integer representation (0-4) or None.
        """
        if v is None:
            return None

        # Priority mapping
        priority_map = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }

        # If already an integer, validate range
        if isinstance(v, int):
            if v < 0 or v > 4:
                raise ValueError("Priority must be between 0 and 4")
            return v

        # If string, convert to integer
        if isinstance(v, str):
            normalized = v.lower().strip()
            if normalized not in priority_map:
                raise ValueError(
                    f"Invalid priority string: '{v}'. "
                    f"Valid values: {', '.join(priority_map.keys())}"
                )
            return priority_map[normalized]

        # Invalid type
        raise ValueError(f"Priority must be an integer (0-4) or string, got {type(v)}")

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate labels are strings and not too long."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("Labels must be a list")
        for label in v:
            if not isinstance(label, str):
                raise ValueError("Each label must be a string")
            if len(label) > 50:
                raise ValueError("Label too long (max 50 characters)")
        return v


class TaskMove(BaseModel):
    """Schema for moving a task to a different column."""

    column_id: UUID = Field(..., description="Target column ID")
    order: float = Field(..., description="New position order")
    version: int = Field(..., description="Current version for optimistic locking")


class TaskResponse(TaskBase):
    """Schema for task response with all fields."""

    id: UUID
    board_id: UUID
    column_id: Optional[UUID]
    order: float
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
