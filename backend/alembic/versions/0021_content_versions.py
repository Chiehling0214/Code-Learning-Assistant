"""Store restorable snapshots before AI content changes.

Revision ID: 0021_content_versions
Revises: 0020_ai_interaction_kind_length
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021_content_versions"
down_revision: str | None = "0020_ai_interaction_kind_length"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(length=16), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_versions_item_id", "content_versions", ["item_id"])
    op.create_index("ix_content_versions_created_by", "content_versions", ["created_by"])
    op.create_index("ix_content_versions_created_at", "content_versions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_content_versions_created_at", table_name="content_versions")
    op.drop_index("ix_content_versions_created_by", table_name="content_versions")
    op.drop_index("ix_content_versions_item_id", table_name="content_versions")
    op.drop_table("content_versions")
