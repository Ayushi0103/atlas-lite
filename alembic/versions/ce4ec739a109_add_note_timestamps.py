"""Add note timestamps

Revision ID: ce4ec739a109
Revises: 827ec3a33aef
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ce4ec739a109"
down_revision: Union[str, Sequence[str], None] = "827ec3a33aef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "note",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.add_column(
        "note",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_column("note", "updated_at")
    op.drop_column("note", "created_at")