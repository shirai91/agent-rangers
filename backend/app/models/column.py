"""Column model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.task import Task


class Column(Base):
    """
    Column model representing a workflow stage in a board.

    Columns use fractional ordering for efficient drag-and-drop repositioning.
    """

    __tablename__ = "columns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        doc="Fractional ordering for drag-and-drop positioning",
    )
    color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
        doc="Hex color code (e.g., #6366f1)",
    )
    wip_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Work-in-progress limit for this column",
    )
    triggers_agents: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="Whether moving a task to this column triggers AI agents",
    )
    is_start_column: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="Whether this is a starting column for new tasks",
    )
    is_end_column: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="Whether this is an ending/done column",
    )
    agent_workflow_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Which workflow to run when task enters: development, quick_development, architecture_only",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
    )

    # Relationships
    board: Mapped["Board"] = relationship(
        "Board",
        back_populates="columns",
        lazy="joined",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="column",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Column(id={self.id}, name='{self.name}', order={self.order})>"
