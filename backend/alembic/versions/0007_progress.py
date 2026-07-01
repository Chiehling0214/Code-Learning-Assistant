"""progress_events table

Revision ID: 0007_progress
Revises: 0006_content_source
Create Date: 2026-07-01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007_progress"
down_revision: str | None = "0006_content_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "progress_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(length=16), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_progress_events_user_id", "progress_events", ["user_id"])
    op.create_index("ix_progress_events_item_id", "progress_events", ["item_id"])
    op.create_index("ix_progress_events_completed_at", "progress_events", ["completed_at"])


def downgrade() -> None:
    op.drop_index("ix_progress_events_completed_at", table_name="progress_events")
    op.drop_index("ix_progress_events_item_id", table_name="progress_events")
    op.drop_index("ix_progress_events_user_id", table_name="progress_events")
    op.drop_table("progress_events")
