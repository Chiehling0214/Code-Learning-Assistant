"""Quiz question explanation (Sprint 14)

Revision ID: 0014_quiz_explanation
Revises: 0013_review_status
Create Date: 2026-07-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014_quiz_explanation"
down_revision: str | None = "0013_review_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("questions", "explanation")
