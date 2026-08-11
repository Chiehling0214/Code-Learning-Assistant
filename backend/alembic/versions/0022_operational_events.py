"""Persist operational monitoring events.

Revision ID: 0022_operational_events
Revises: 0021_content_versions
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022_operational_events"
down_revision: str | None = "0021_content_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "operational_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operational_events_category", "operational_events", ["category"])
    op.create_index("ix_operational_events_created_at", "operational_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_operational_events_created_at", table_name="operational_events")
    op.drop_index("ix_operational_events_category", table_name="operational_events")
    op.drop_table("operational_events")
