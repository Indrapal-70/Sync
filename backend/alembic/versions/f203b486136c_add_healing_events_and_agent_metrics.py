"""add_healing_events_and_agent_metrics

Revision ID: f203b486136c
Revises: 2d7d7114c857
Create Date: 2026-06-20 13:49:00.154389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f203b486136c'
down_revision: Union[str, Sequence[str], None] = '2d7d7114c857'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create healing_events table
    op.create_table(
        'healing_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('cycle', sa.Integer(), nullable=False),
        sa.Column('failed_agent', sa.String(), nullable=False),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('injected_node_ids', sa.JSON(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_healing_events_task_id', 'healing_events', ['task_id'], unique=False)

    # Create agent_metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=False),
        sa.Column('step', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=False),
        sa.Column('healing_cycle', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_metrics_task_id', 'agent_metrics', ['task_id'], unique=False)
    op.create_index('ix_agent_metrics_agent_name', 'agent_metrics', ['agent_name'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_agent_metrics_agent_name', table_name='agent_metrics')
    op.drop_index('ix_agent_metrics_task_id', table_name='agent_metrics')
    op.drop_table('agent_metrics')
    op.drop_index('ix_healing_events_task_id', table_name='healing_events')
    op.drop_table('healing_events')
