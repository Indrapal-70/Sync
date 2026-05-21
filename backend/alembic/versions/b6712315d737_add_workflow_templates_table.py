"""Add workflow_templates table

Revision ID: b6712315d737
Revises: 8de181d7091e
Create Date: 2026-05-21 17:23:12.523920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b6712315d737'
down_revision: Union[str, Sequence[str], None] = '8de181d7091e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('workflow_templates',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('tasks_schema', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_templates_name'), 'workflow_templates', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_workflow_templates_name'), table_name='workflow_templates')
    op.drop_table('workflow_templates')

