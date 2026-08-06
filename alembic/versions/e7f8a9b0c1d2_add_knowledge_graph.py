"""add knowledge graph

Revision ID: e7f8a9b0c1d2
Revises: c1d2e3f4a5b6
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "knowledge_graph_node",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(collation="NOCASE"), nullable=False),
        sa.Column("type", sa.String(collation="NOCASE"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name",
            "type",
            name="uq_knowledge_graph_node_name_type",
        ),
    )
    op.create_table(
        "knowledge_graph_edge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=False),
        sa.Column("relationship", sa.String(collation="NOCASE"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["source_node_id"],
            ["knowledge_graph_node.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"],
            ["knowledge_graph_node.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_node_id",
            "target_node_id",
            "relationship",
            name="uq_knowledge_graph_edge_relationship",
        ),
    )
    op.create_index(
        op.f("ix_knowledge_graph_edge_source_node_id"),
        "knowledge_graph_edge",
        ["source_node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_graph_edge_target_node_id"),
        "knowledge_graph_edge",
        ["target_node_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_knowledge_graph_edge_target_node_id"),
        table_name="knowledge_graph_edge",
    )
    op.drop_index(
        op.f("ix_knowledge_graph_edge_source_node_id"),
        table_name="knowledge_graph_edge",
    )
    op.drop_table("knowledge_graph_edge")
    op.drop_table("knowledge_graph_node")
