"""Agent execution schema: agent_executions, agent_outputs, and task agent fields

Revision ID: 003_agent_execution
Revises: 002_workflow_engine
Create Date: 2026-02-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_agent_execution'
down_revision: Union[str, None] = '002_workflow_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agent execution tables and update tasks table."""

    # Add agent-related columns to tasks table
    op.add_column(
        'tasks',
        sa.Column('agent_status', sa.String(length=50), nullable=True,
                  comment='Agent processing status: pending, architecture, development, review, completed, failed')
    )
    op.add_column(
        'tasks',
        sa.Column('current_execution_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='Reference to the current/latest agent execution')
    )
    op.add_column(
        'tasks',
        sa.Column('agent_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default='{}', comment='Additional agent-related metadata')
    )

    # Create agent_executions table
    op.create_table(
        'agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('board_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_type', sa.String(length=50), nullable=False,
                  comment='development, quick_development, architecture_only'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending',
                  comment='pending, running, completed, failed, cancelled'),
        sa.Column('current_phase', sa.String(length=50), nullable=True,
                  comment='Current workflow phase: architecture, development, review'),
        sa.Column('iteration', sa.Integer(), nullable=False, server_default='1',
                  comment='Current iteration count for feedback loops'),
        sa.Column('max_iterations', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default='{}', comment='Execution context and configuration'),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                  comment='Summary of execution results'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_executions_id'), 'agent_executions', ['id'], unique=False)
    op.create_index(op.f('ix_agent_executions_task_id'), 'agent_executions', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_board_id'), 'agent_executions', ['board_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_status'), 'agent_executions', ['status'], unique=False)
    op.create_index(op.f('ix_agent_executions_created_at'), 'agent_executions', ['created_at'], unique=False)

    # Add foreign key from tasks.current_execution_id to agent_executions.id
    # Note: This is added after agent_executions table is created
    op.create_foreign_key(
        'fk_tasks_current_execution_id',
        'tasks', 'agent_executions',
        ['current_execution_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create agent_outputs table
    op.create_table(
        'agent_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False,
                  comment='software-architect, software-developer, code-reviewer, queen-coordinator'),
        sa.Column('phase', sa.String(length=50), nullable=False,
                  comment='architecture, development, review'),
        sa.Column('iteration', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending',
                  comment='pending, running, completed, failed'),
        sa.Column('input_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default='{}', comment='Input provided to the agent'),
        sa.Column('output_content', sa.Text(), nullable=True,
                  comment='Raw text output from the agent'),
        sa.Column('output_structured', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                  comment='Parsed structured output'),
        sa.Column('files_created', postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default='[]', comment='List of files created/modified by agent'),
        sa.Column('tokens_used', sa.Integer(), nullable=True,
                  comment='Total tokens used in this agent call'),
        sa.Column('duration_ms', sa.Integer(), nullable=True,
                  comment='Execution duration in milliseconds'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['execution_id'], ['agent_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_outputs_id'), 'agent_outputs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_outputs_execution_id'), 'agent_outputs', ['execution_id'], unique=False)
    op.create_index(op.f('ix_agent_outputs_task_id'), 'agent_outputs', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_outputs_agent_name'), 'agent_outputs', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_outputs_phase'), 'agent_outputs', ['phase'], unique=False)
    op.create_index(op.f('ix_agent_outputs_created_at'), 'agent_outputs', ['created_at'], unique=False)

    # Add agent configuration columns to columns table
    op.add_column(
        'columns',
        sa.Column('agent_workflow_type', sa.String(length=50), nullable=True,
                  comment='Which workflow to run when task enters: development, quick_development, architecture_only')
    )


def downgrade() -> None:
    """Drop agent execution tables and columns."""

    # Remove agent configuration from columns table
    op.drop_column('columns', 'agent_workflow_type')

    # Drop agent_outputs table
    op.drop_index(op.f('ix_agent_outputs_created_at'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_phase'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_agent_name'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_task_id'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_execution_id'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_id'), table_name='agent_outputs')
    op.drop_table('agent_outputs')

    # Remove foreign key from tasks before dropping agent_executions
    op.drop_constraint('fk_tasks_current_execution_id', 'tasks', type_='foreignkey')

    # Drop agent_executions table
    op.drop_index(op.f('ix_agent_executions_created_at'), table_name='agent_executions')
    op.drop_index(op.f('ix_agent_executions_status'), table_name='agent_executions')
    op.drop_index(op.f('ix_agent_executions_board_id'), table_name='agent_executions')
    op.drop_index(op.f('ix_agent_executions_task_id'), table_name='agent_executions')
    op.drop_index(op.f('ix_agent_executions_id'), table_name='agent_executions')
    op.drop_table('agent_executions')

    # Remove agent columns from tasks table
    op.drop_column('tasks', 'agent_metadata')
    op.drop_column('tasks', 'current_execution_id')
    op.drop_column('tasks', 'agent_status')
