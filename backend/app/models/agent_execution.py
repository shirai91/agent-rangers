"""AgentExecution model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.task import Task
    from app.models.agent_output import AgentOutput


class AgentExecution(Base):
    """
    AgentExecution model representing a complete agent workflow execution.

    An execution tracks the full lifecycle of running agents (architect, developer, reviewer)
    on a task, including multiple iterations for feedback loops.
    """

    __tablename__ = "agent_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="development, quick_development, architecture_only",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        doc="pending, running, completed, failed, cancelled, awaiting_clarification",
    )
    current_phase: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Current workflow phase: architecture, development, review",
    )
    iteration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        doc="Current iteration count for feedback loops",
    )
    max_iterations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    clarification_questions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Clarification questions from clarity check: {questions: [...], summary: str, confidence: float}",
    )
    clarification_answers: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="User answers to clarification questions",
    )
    context: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        doc="Execution context and configuration",
    )
    result_summary: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Summary of execution results",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="executions",
        foreign_keys=[task_id],
        lazy="joined",
    )
    board: Mapped["Board"] = relationship(
        "Board",
        back_populates="agent_executions",
        lazy="joined",
    )
    outputs: Mapped[list["AgentOutput"]] = relationship(
        "AgentOutput",
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AgentOutput.created_at",
    )

    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, task_id={self.task_id}, status='{self.status}', phase='{self.current_phase}')>"
