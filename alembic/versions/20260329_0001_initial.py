"""initial tables

Revision ID: 20260329_0001
Revises:
Create Date: 2026-03-29 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "memory_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        if_not_exists=True,
    )

    op.create_table(
        "consents",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("gpc_enabled", sa.Integer(), nullable=False),
        sa.Column("one_click_opt_out", sa.Integer(), nullable=False),
        sa.Column("voice_enabled", sa.Integer(), nullable=False),
        sa.Column("vision_enabled", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        if_not_exists=True,
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("consents")
    op.drop_table("memory_records")
