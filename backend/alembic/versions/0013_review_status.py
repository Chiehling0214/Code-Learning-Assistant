"""Lesson review_status for admin AI-content review (Sprint 13)

Revision ID: 0013_review_status
Revises: 0012_course_chat
Create Date: 2026-07-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013_review_status"
down_revision: str | None = "0012_course_chat"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column(
            "review_status",
            sa.String(length=16),
            nullable=False,
            server_default="approved",
        ),
    )
    # Existing AI-authored lessons enter the review queue as "pending".
    op.execute("UPDATE lessons SET review_status = 'pending' WHERE source = 'ai'")


def downgrade() -> None:
    op.drop_column("lessons", "review_status")
