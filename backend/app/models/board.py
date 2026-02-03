"""Board model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.column import Column
    from app.models.task import Task
    from app.models.workflow_definition import WorkflowDefinition


class Board(Base):
    """
    Board model representing a Kanban board.

    A board contains columns and tasks organized in a workflow.
    """

    __tablename__ = "boards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
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
    columns: Mapped[list["Column"]] = relationship(
        "Column",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    workflow_definitions: Mapped[list["WorkflowDefinition"]] = relationship(
        "WorkflowDefinition",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Board(id={self.id}, name='{self.name}')>"
