"""Add synced drafts, mistake notes, and generation notification state.

Revision ID: 0018_learning_tools
Revises: 0017_learning_resume
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_learning_tools"
down_revision: str | None = "0017_learning_resume"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "review_items", sa.Column("note", sa.Text(), server_default="", nullable=False)
    )
    op.add_column(
        "generation_jobs",
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "code_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exercise_id", name="uq_code_drafts_user_exercise"),
    )
    op.create_index("ix_code_drafts_user_id", "code_drafts", ["user_id"])
    op.create_index("ix_code_drafts_exercise_id", "code_drafts", ["exercise_id"])


def downgrade() -> None:
    op.drop_index("ix_code_drafts_exercise_id", table_name="code_drafts")
    op.drop_index("ix_code_drafts_user_id", table_name="code_drafts")
    op.drop_table("code_drafts")
    op.drop_column("generation_jobs", "seen_at")
    op.drop_column("review_items", "note")
