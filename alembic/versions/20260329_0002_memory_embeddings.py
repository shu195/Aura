"""add memory embeddings table

Revision ID: 20260329_0002
Revises: 20260329_0001
Create Date: 2026-03-29 00:10:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260329_0002"
down_revision: Union[str, Sequence[str], None] = "20260329_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "memory_embeddings",
        sa.Column("record_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["memory_records.id"], ondelete="CASCADE"),
        if_not_exists=True,
    )
    op.create_index("idx_memory_embeddings_user_id", "memory_embeddings", ["user_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index("idx_memory_embeddings_user_id", table_name="memory_embeddings")
    op.drop_table("memory_embeddings")
