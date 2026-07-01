"""source column on lessons and exercises

Revision ID: 0006_content_source
Revises: 0005_ai_interactions
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_content_source"
down_revision: str | None = "0005_ai_interactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("source", sa.String(length=16), nullable=False, server_default="human"),
    )
    op.add_column(
        "exercises",
        sa.Column("source", sa.String(length=16), nullable=False, server_default="human"),
    )


def downgrade() -> None:
    op.drop_column("exercises", "source")
    op.drop_column("lessons", "source")
