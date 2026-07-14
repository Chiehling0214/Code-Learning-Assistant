"""courses.kind for practice drill containers (Sprint 16)

Revision ID: 0016_course_kind
Revises: 0015_review_items
Create Date: 2026-07-06

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016_course_kind"
down_revision: str | None = "0015_review_items"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="course"),
    )


def downgrade() -> None:
    op.drop_column("courses", "kind")
