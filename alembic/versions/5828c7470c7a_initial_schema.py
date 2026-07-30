"""Initial schema

Revision ID: 5828c7470c7a
Revises: 
Create Date: 2026-07-29 22:46:25.126570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5828c7470c7a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "note",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("note")
