"""add document source url

Revision ID: a4f8c2d7b901
Revises: 58bf449e4f3f
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4f8c2d7b901"
down_revision: Union[str, Sequence[str], None] = "58bf449e4f3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("document", sa.Column("source_url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("document", "source_url")
