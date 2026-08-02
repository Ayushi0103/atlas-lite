"""add semantic search chroma

Revision ID: d5f6a7b8c901
Revises: a4f8c2d7b901
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union


revision: str = "d5f6a7b8c901"
down_revision: Union[str, Sequence[str], None] = "a4f8c2d7b901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Semantic vectors are stored in ChromaDB, not SQLite."""
    pass


def downgrade() -> None:
    """No SQLite schema changes to reverse."""
    pass
