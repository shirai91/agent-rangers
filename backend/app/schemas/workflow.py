"""Pydantic schemas for Workflow models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# WorkflowDefinition Schemas
# ============================================================================

class WorkflowDefinitionBase(BaseModel):
    """Base schema for WorkflowDefinition with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    is_active: bool = Field(True, description="Whether workflow is currently active")
    settings: dict = Field(default_factory=dict, description="Additional workflow settings")


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    """Schema for creating a new workflow definition."""
    pass


class WorkflowDefinitionUpdate(BaseModel):
    """Schema for updating a workflow definition (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    """Schema for workflow definition response with all fields."""

    id: UUID
    board_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WorkflowTransition Schemas
# ============================================================================

class WorkflowTransitionBase(BaseModel):
    """Base schema for WorkflowTransition with common fields."""

    from_column_id: UUID = Field(..., description="Source column ID")
    to_column_id: UUID = Field(..., description="Target column ID")
    name: Optional[str] = Field(None, max_length=255, description="Optional transition name")
    is_enabled: bool = Field(True, description="Whether transition is enabled")
    conditions: dict = Field(default_factory=dict, description="Conditions for this transition")


class WorkflowTransitionCreate(WorkflowTransitionBase):
    """Schema for creating a new workflow transition."""
    pass


class WorkflowTransitionUpdate(BaseModel):
    """Schema for updating a workflow transition (all fields optional)."""

    name: Optional[str] = Field(None, max_length=255)
    is_enabled: Optional[bool] = None
    conditions: Optional[dict] = None


class WorkflowTransitionResponse(WorkflowTransitionBase):
    """Schema for workflow transition response with all fields."""

    id: UUID
    workflow_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowTransitionWithColumnsResponse(WorkflowTransitionResponse):
    """Schema for workflow transition response with column names."""

    from_column_name: Optional[str] = None
    to_column_name: Optional[str] = None


# ============================================================================
# Full Workflow Response (with transitions)
# ============================================================================

class WorkflowDefinitionWithTransitionsResponse(WorkflowDefinitionResponse):
    """Schema for workflow definition response including all transitions."""

    transitions: List[WorkflowTransitionResponse] = []


# ============================================================================
# Allowed Targets Response
# ============================================================================

class AllowedTargetResponse(BaseModel):
    """Schema for allowed move targets for a task."""

    column_id: UUID
    column_name: str


class AllowedTransitionsResponse(BaseModel):
    """Schema for all allowed transitions from a column."""

    from_column_id: UUID
    allowed_targets: List[AllowedTargetResponse]
