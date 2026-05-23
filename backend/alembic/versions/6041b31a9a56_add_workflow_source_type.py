"""add workflow source_type

Revision ID: 6041b31a9a56
Revises: b6712315d737
Create Date: 2026-05-23 14:31:44.194017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6041b31a9a56'
down_revision: Union[str, Sequence[str], None] = 'b6712315d737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('workflows', sa.Column('source_type', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('workflows', 'source_type')
