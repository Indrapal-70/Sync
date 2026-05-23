"""add node_id to tasks

Revision ID: 2d7d7114c857
Revises: 6041b31a9a56
Create Date: 2026-05-23 15:00:35.434112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2d7d7114c857'
down_revision: Union[str, Sequence[str], None] = '6041b31a9a56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('node_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tasks', 'node_id')
