"""Pydantic schemas for API request/response validation."""

from app.schemas.board import (
    BoardBase,
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    BoardListResponse,
)
from app.schemas.column import (
    ColumnBase,
    ColumnCreate,
    ColumnUpdate,
    ColumnResponse,
)
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskMove,
    TaskResponse,
)
from app.schemas.workflow import (
    WorkflowDefinitionBase,
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionResponse,
    WorkflowDefinitionWithTransitionsResponse,
    WorkflowTransitionBase,
    WorkflowTransitionCreate,
    WorkflowTransitionUpdate,
    WorkflowTransitionResponse,
    WorkflowTransitionWithColumnsResponse,
    AllowedTargetResponse,
    AllowedTransitionsResponse,
)
from app.schemas.activity import (
    TaskActivityBase,
    TaskActivityCreate,
    TaskActivityResponse,
    TaskActivityListResponse,
    BoardActivityResponse,
)

__all__ = [
    # Board
    "BoardBase",
    "BoardCreate",
    "BoardUpdate",
    "BoardResponse",
    "BoardListResponse",
    # Column
    "ColumnBase",
    "ColumnCreate",
    "ColumnUpdate",
    "ColumnResponse",
    # Task
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskMove",
    "TaskResponse",
    # Workflow
    "WorkflowDefinitionBase",
    "WorkflowDefinitionCreate",
    "WorkflowDefinitionUpdate",
    "WorkflowDefinitionResponse",
    "WorkflowDefinitionWithTransitionsResponse",
    "WorkflowTransitionBase",
    "WorkflowTransitionCreate",
    "WorkflowTransitionUpdate",
    "WorkflowTransitionResponse",
    "WorkflowTransitionWithColumnsResponse",
    "AllowedTargetResponse",
    "AllowedTransitionsResponse",
    # Activity
    "TaskActivityBase",
    "TaskActivityCreate",
    "TaskActivityResponse",
    "TaskActivityListResponse",
    "BoardActivityResponse",
]
