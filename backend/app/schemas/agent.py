"""Pydantic schemas for Agent execution models."""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class StartAgentWorkflowRequest(BaseModel):
    """Schema for starting an agent workflow."""

    workflow_type: str = Field(
        default="development",
        description="Workflow type: development, quick_development, architecture_only",
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional execution context",
    )


class AgentOutputResponse(BaseModel):
    """Schema for agent output response."""

    id: UUID
    execution_id: UUID
    task_id: UUID
    agent_name: str
    phase: str
    iteration: int
    status: str
    input_context: dict[str, Any]
    output_content: Optional[str]
    output_structured: Optional[dict[str, Any]]
    files_created: list[Any]
    tokens_used: Optional[int]
    duration_ms: Optional[int]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution response with outputs."""

    id: UUID
    task_id: UUID
    board_id: UUID
    workflow_type: str
    status: str
    current_phase: Optional[str]
    iteration: int
    max_iterations: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    context: dict[str, Any]
    result_summary: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    outputs: list[AgentOutputResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExecutionStatusResponse(BaseModel):
    """Schema for execution status response (lightweight)."""

    execution_id: UUID
    task_id: UUID
    workflow_type: str
    status: str
    current_phase: Optional[str]
    iteration: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    outputs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Lightweight output status list",
    )

    model_config = ConfigDict(from_attributes=True)
