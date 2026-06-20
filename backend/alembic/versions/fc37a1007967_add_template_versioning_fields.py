"""add_template_versioning_fields

Revision ID: fc37a1007967
Revises: f203b486136c
Create Date: 2026-06-20 13:56:56.775855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fc37a1007967'
down_revision: Union[str, Sequence[str], None] = 'f203b486136c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('workflow_templates', sa.Column('version', sa.String(), nullable=False, server_default='1.0.0'))
    op.add_column('workflow_templates', sa.Column('parent_template_id', sa.String(), nullable=True))
    op.add_column('workflow_templates', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('workflow_templates', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('workflow_templates', sa.Column('author', sa.String(), nullable=True))
    op.add_column('workflow_templates', sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('workflow_templates', 'usage_count')
    op.drop_column('workflow_templates', 'author')
    op.drop_column('workflow_templates', 'tags')
    op.drop_column('workflow_templates', 'is_public')
    op.drop_column('workflow_templates', 'parent_template_id')
    op.drop_column('workflow_templates', 'version')

