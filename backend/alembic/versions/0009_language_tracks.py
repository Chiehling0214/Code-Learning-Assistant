"""language_tracks table

Revision ID: 0009_language_tracks
Revises: 0008_subscriptions
Create Date: 2026-07-01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0009_language_tracks"
down_revision: str | None = "0008_subscriptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "language_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["language_id"], ["programming_languages.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "language_id", name="uq_language_tracks_user_language"),
    )
    op.create_index("ix_language_tracks_user_id", "language_tracks", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_language_tracks_user_id", table_name="language_tracks")
    op.drop_table("language_tracks")
