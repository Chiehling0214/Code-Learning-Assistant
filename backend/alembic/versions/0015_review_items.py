"""Spaced review of mistakes (Sprint 15)

Revision ID: 0015_review_items
Revises: 0014_quiz_explanation
Create Date: 2026-07-06

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0015_review_items"
down_revision: str | None = "0014_quiz_explanation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("item_ref", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retired", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "item_ref", name="uq_review_items_user_ref"),
    )
    op.create_index("ix_review_items_user_id", "review_items", ["user_id"])
    op.create_index("ix_review_items_due_at", "review_items", ["due_at"])


def downgrade() -> None:
    op.drop_index("ix_review_items_due_at", table_name="review_items")
    op.drop_index("ix_review_items_user_id", table_name="review_items")
    op.drop_table("review_items")
