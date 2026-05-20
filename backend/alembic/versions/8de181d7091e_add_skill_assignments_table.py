"""add skill_assignments table

Revision ID: 8de181d7091e
Revises: 
Create Date: 2026-05-21 03:09:10.151942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8de181d7091e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — only creates skill_assignments table."""
    op.create_table(
        'skill_assignments',
        sa.Column('skill_name', sa.String(), nullable=False),
        sa.Column('model_key', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('skill_name'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('skill_assignments')
