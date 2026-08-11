"""Allow descriptive AI interaction kinds.

Revision ID: 0020_ai_interaction_kind_length
Revises: 0019_core_learning_workflows
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020_ai_interaction_kind_length"
down_revision: str | None = "0019_core_learning_workflows"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "ai_interactions",
        "kind",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "ai_interactions",
        "kind",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=False,
    )
