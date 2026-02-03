"""Initial schema with boards, columns, and tasks

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-03 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema for Agent Rangers."""

    # Create boards table
    op.create_table(
        'boards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boards_id'), 'boards', ['id'], unique=False)

    # Create columns table
    op.create_table(
        'columns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('board_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('order', sa.Float(), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('wip_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_columns_id'), 'columns', ['id'], unique=False)
    op.create_index(op.f('ix_columns_board_id'), 'columns', ['board_id'], unique=False)
    op.create_index(op.f('ix_columns_order'), 'columns', ['order'], unique=False)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('board_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('column_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Float(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('labels', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['column_id'], ['columns.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_board_id'), 'tasks', ['board_id'], unique=False)
    op.create_index(op.f('ix_tasks_column_id'), 'tasks', ['column_id'], unique=False)
    op.create_index(op.f('ix_tasks_order'), 'tasks', ['order'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_tasks_order'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_column_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_board_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')

    op.drop_index(op.f('ix_columns_order'), table_name='columns')
    op.drop_index(op.f('ix_columns_board_id'), table_name='columns')
    op.drop_index(op.f('ix_columns_id'), table_name='columns')
    op.drop_table('columns')

    op.drop_index(op.f('ix_boards_id'), table_name='boards')
    op.drop_table('boards')
