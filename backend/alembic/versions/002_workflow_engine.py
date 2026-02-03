"""Workflow engine schema: workflow definitions, transitions, and task activities

Revision ID: 002_workflow_engine
Revises: 001_initial_schema
Create Date: 2026-02-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_workflow_engine'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workflow engine tables and update columns table."""

    # Add new columns to columns table for workflow features
    op.add_column(
        'columns',
        sa.Column('triggers_agents', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'columns',
        sa.Column('is_start_column', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'columns',
        sa.Column('is_end_column', sa.Boolean(), nullable=False, server_default='false')
    )

    # Create workflow_definitions table
    op.create_table(
        'workflow_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('board_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_definitions_id'), 'workflow_definitions', ['id'], unique=False)
    op.create_index(op.f('ix_workflow_definitions_board_id'), 'workflow_definitions', ['board_id'], unique=False)

    # Create workflow_transitions table
    op.create_table(
        'workflow_transitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_column_id'], ['columns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_column_id'], ['columns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'from_column_id', 'to_column_id', name='uq_workflow_transition')
    )
    op.create_index(op.f('ix_workflow_transitions_id'), 'workflow_transitions', ['id'], unique=False)
    op.create_index(op.f('ix_workflow_transitions_workflow_id'), 'workflow_transitions', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_workflow_transitions_from_column_id'), 'workflow_transitions', ['from_column_id'], unique=False)
    op.create_index(op.f('ix_workflow_transitions_to_column_id'), 'workflow_transitions', ['to_column_id'], unique=False)

    # Create task_activities table
    op.create_table(
        'task_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('board_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=False, server_default='system'),
        sa.Column('from_column_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_column_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_column_id'], ['columns.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_column_id'], ['columns.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_activities_id'), 'task_activities', ['id'], unique=False)
    op.create_index(op.f('ix_task_activities_task_id'), 'task_activities', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_activities_board_id'), 'task_activities', ['board_id'], unique=False)
    op.create_index(op.f('ix_task_activities_created_at'), 'task_activities', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop workflow engine tables and columns."""

    # Drop task_activities table
    op.drop_index(op.f('ix_task_activities_created_at'), table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_board_id'), table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_task_id'), table_name='task_activities')
    op.drop_index(op.f('ix_task_activities_id'), table_name='task_activities')
    op.drop_table('task_activities')

    # Drop workflow_transitions table
    op.drop_index(op.f('ix_workflow_transitions_to_column_id'), table_name='workflow_transitions')
    op.drop_index(op.f('ix_workflow_transitions_from_column_id'), table_name='workflow_transitions')
    op.drop_index(op.f('ix_workflow_transitions_workflow_id'), table_name='workflow_transitions')
    op.drop_index(op.f('ix_workflow_transitions_id'), table_name='workflow_transitions')
    op.drop_table('workflow_transitions')

    # Drop workflow_definitions table
    op.drop_index(op.f('ix_workflow_definitions_board_id'), table_name='workflow_definitions')
    op.drop_index(op.f('ix_workflow_definitions_id'), table_name='workflow_definitions')
    op.drop_table('workflow_definitions')

    # Remove columns from columns table
    op.drop_column('columns', 'is_end_column')
    op.drop_column('columns', 'is_start_column')
    op.drop_column('columns', 'triggers_agents')
