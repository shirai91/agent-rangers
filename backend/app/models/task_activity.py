"""TaskActivity model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.board import Board
    from app.models.column import Column


class TaskActivity(Base):
    """
    TaskActivity model representing the history of changes to a task.

    Tracks all modifications including creation, updates, moves, and deletions.
    """

    __tablename__ = "task_activities"

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
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of activity: created, updated, moved, deleted, comment, etc.",
    )
    actor: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="system",
        server_default="system",
        doc="Who performed the action (user id, agent name, or 'system')",
    )
    from_column_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("columns.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source column for move activities",
    )
    to_column_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("columns.id", ondelete="SET NULL"),
        nullable=True,
        doc="Target column for move activities",
    )
    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Previous value(s) before the change",
    )
    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="New value(s) after the change",
    )
    activity_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        doc="Additional metadata about the activity",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="activities",
        lazy="joined",
    )
    board: Mapped["Board"] = relationship(
        "Board",
        lazy="joined",
    )
    from_column: Mapped["Column | None"] = relationship(
        "Column",
        foreign_keys=[from_column_id],
        lazy="joined",
    )
    to_column: Mapped["Column | None"] = relationship(
        "Column",
        foreign_keys=[to_column_id],
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<TaskActivity(id={self.id}, task_id={self.task_id}, type='{self.activity_type}')>"
