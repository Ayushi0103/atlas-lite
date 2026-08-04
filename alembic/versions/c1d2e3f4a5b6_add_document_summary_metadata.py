"""add document summary metadata

Revision ID: c1d2e3f4a5b6
Revises: 9f0b1c2d3e4f
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "9f0b1c2d3e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("document", sa.Column("short_summary", sa.Text(), nullable=True))
    op.add_column("document", sa.Column("detailed_summary", sa.Text(), nullable=True))
    op.add_column("document", sa.Column("key_concepts", sa.Text(), nullable=True))
    op.add_column("document", sa.Column("keywords", sa.Text(), nullable=True))
    op.add_column(
        "document",
        sa.Column("suggested_questions", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("document", "suggested_questions")
    op.drop_column("document", "keywords")
    op.drop_column("document", "key_concepts")
    op.drop_column("document", "detailed_summary")
    op.drop_column("document", "short_summary")
