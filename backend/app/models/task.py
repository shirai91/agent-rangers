"""Task model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Float, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.column import Column
    from app.models.task_activity import TaskActivity


class Task(Base):
    """
    Task model representing a work item in the Kanban board.

    Tasks use fractional ordering for efficient positioning within columns
    and version numbers for optimistic locking.
    """

    __tablename__ = "tasks"

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
    column_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("columns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        doc="Position within column using fractional ordering",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="0=none, 1=low, 2=medium, 3=high, 4=urgent",
    )
    labels: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc="Array of label strings",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        doc="Version number for optimistic locking",
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
        back_populates="tasks",
        lazy="joined",
    )
    column: Mapped["Column | None"] = relationship(
        "Column",
        back_populates="tasks",
        lazy="joined",
    )
    activities: Mapped[list["TaskActivity"]] = relationship(
        "TaskActivity",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="noload",
        order_by="TaskActivity.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title[:30]}...', version={self.version})>"
