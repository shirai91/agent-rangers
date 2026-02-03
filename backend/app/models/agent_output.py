"""AgentOutput model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.agent_execution import AgentExecution


class AgentOutput(Base):
    """
    AgentOutput model representing a single agent's output within an execution.

    Each output captures the input, output, and metrics from one agent
    (architect, developer, or reviewer) during one phase of a workflow.
    """

    __tablename__ = "agent_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="software-architect, software-developer, code-reviewer, queen-coordinator",
    )
    phase: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="architecture, development, review",
    )
    iteration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        doc="pending, running, completed, failed",
    )
    input_context: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        doc="Input provided to the agent",
    )
    output_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Raw text output from the agent",
    )
    output_structured: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Parsed structured output",
    )
    files_created: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc="List of files created/modified by agent",
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Total tokens used in this agent call",
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Execution duration in milliseconds",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    execution: Mapped["AgentExecution"] = relationship(
        "AgentExecution",
        back_populates="outputs",
        lazy="joined",
    )
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="agent_outputs",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<AgentOutput(id={self.id}, agent='{self.agent_name}', phase='{self.phase}', status='{self.status}')>"
