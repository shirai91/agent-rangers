"""WorkflowDefinition model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.workflow_transition import WorkflowTransition


class WorkflowDefinition(Base):
    """
    WorkflowDefinition model representing workflow rules for a board.

    Defines the valid transitions between columns in a Kanban board.
    """

    __tablename__ = "workflow_definitions"

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
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="Whether this workflow is currently active",
    )
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        doc="Additional workflow settings (e.g., strict mode)",
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
        back_populates="workflow_definitions",
        lazy="joined",
    )
    transitions: Mapped[list["WorkflowTransition"]] = relationship(
        "WorkflowTransition",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', is_active={self.is_active})>"
