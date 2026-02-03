"""Pydantic schemas for Board model."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.column import ColumnResponse


class BoardBase(BaseModel):
    """Base schema for Board with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Board name")
    description: Optional[str] = Field(None, description="Board description")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Board settings as JSON")


class BoardCreate(BoardBase):
    """Schema for creating a new board."""

    pass


class BoardUpdate(BaseModel):
    """Schema for updating a board (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class BoardResponse(BoardBase):
    """Schema for board response with all fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    columns: list[ColumnResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BoardListResponse(BaseModel):
    """Schema for list of boards (without columns for performance)."""

    id: UUID
    name: str
    description: Optional[str]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
