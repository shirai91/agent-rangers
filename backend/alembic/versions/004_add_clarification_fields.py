"""add clarification fields to agent_executions

Revision ID: 004_clarification
Revises: be04ffcfddf1
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_clarification'
down_revision: Union[str, None] = 'be04ffcfddf1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'agent_executions',
        sa.Column('clarification_questions', postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        'agent_executions',
        sa.Column('clarification_answers', postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('agent_executions', 'clarification_answers')
    op.drop_column('agent_executions', 'clarification_questions')
