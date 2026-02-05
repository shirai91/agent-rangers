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
    working_directory: Optional[str] = Field(None, max_length=1024, description="Working directory path")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Board settings as JSON")


class BoardCreate(BoardBase):
    """Schema for creating a new board."""

    pass


class BoardUpdate(BaseModel):
    """Schema for updating a board (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    working_directory: Optional[str] = Field(None, max_length=1024)
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
    working_directory: Optional[str]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkingDirectoryUpdate(BaseModel):
    """Schema for updating a board's working directory."""

    working_directory: str = Field(..., min_length=1, max_length=1024, description="Working directory path")


class RepositoryInfo(BaseModel):
    """Schema for repository information."""

    name: str
    path: str
    remote_url: Optional[str] = None
    primary_language: Optional[str] = None
    file_counts: Dict[str, int] = Field(default_factory=dict)


class RepositoryListResponse(BaseModel):
    """Schema for list of repositories."""

    repositories: list[RepositoryInfo]
    count: int
