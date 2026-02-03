"""WorkflowTransition model for Agent Rangers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.workflow_definition import WorkflowDefinition
    from app.models.column import Column


class WorkflowTransition(Base):
    """
    WorkflowTransition model representing allowed transitions between columns.

    Each transition defines a valid move from one column to another.
    """

    __tablename__ = "workflow_transitions"
    __table_args__ = (
        UniqueConstraint(
            "workflow_id", "from_column_id", "to_column_id",
            name="uq_workflow_transition"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional name for this transition (e.g., 'Start Development')",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="Whether this transition is currently enabled",
    )
    conditions: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        doc="Conditions that must be met for transition (e.g., required fields)",
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
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="transitions",
        lazy="joined",
    )
    from_column: Mapped["Column"] = relationship(
        "Column",
        foreign_keys=[from_column_id],
        lazy="joined",
    )
    to_column: Mapped["Column"] = relationship(
        "Column",
        foreign_keys=[to_column_id],
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<WorkflowTransition(id={self.id}, from={self.from_column_id}, to={self.to_column_id})>"
