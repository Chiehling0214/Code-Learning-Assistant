"""Durable generation, course pathways, and content reports.

Revision ID: 0019_core_learning_workflows
Revises: 0018_learning_tools
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_core_learning_workflows"
down_revision: str | None = "0018_learning_tools"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generation_jobs", sa.Column("kind", sa.String(24), server_default="initial", nullable=False))
    op.add_column("generation_jobs", sa.Column("course_count", sa.Integer(), server_default="1", nullable=False))
    op.add_column("generation_jobs", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("generation_jobs", sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False))
    op.add_column("generation_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("generation_jobs", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("generation_jobs", sa.Column("cancel_requested", sa.Boolean(), server_default=sa.false(), nullable=False))

    op.add_column("courses", sa.Column("prerequisite_course_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("courses", sa.Column("sequence_index", sa.Integer(), server_default="0", nullable=False))
    op.add_column("courses", sa.Column("recommendation_reason", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("generation_job_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_courses_prerequisite", "courses", "courses", ["prerequisite_course_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_courses_generation_job", "courses", "generation_jobs", ["generation_job_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_courses_generation_job_id", "courses", ["generation_job_id"])

    op.create_table(
        "content_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(16), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("details", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(16), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_reports_user_id", "content_reports", ["user_id"])
    op.create_index("ix_content_reports_item_id", "content_reports", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_content_reports_item_id", table_name="content_reports")
    op.drop_index("ix_content_reports_user_id", table_name="content_reports")
    op.drop_table("content_reports")
    op.drop_index("ix_courses_generation_job_id", table_name="courses")
    op.drop_constraint("fk_courses_generation_job", "courses", type_="foreignkey")
    op.drop_constraint("fk_courses_prerequisite", "courses", type_="foreignkey")
    for column in ("generation_job_id", "recommendation_reason", "sequence_index", "prerequisite_course_id"):
        op.drop_column("courses", column)
    for column in ("cancel_requested", "next_attempt_at", "heartbeat_at", "max_attempts", "attempt_count", "course_count", "kind"):
        op.drop_column("generation_jobs", column)
