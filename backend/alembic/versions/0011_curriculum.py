"""AI curriculum: courses.track_id + generation_jobs

Revision ID: 0011_curriculum
Revises: 0010_placement
Create Date: 2026-07-01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0011_curriculum"
down_revision: str | None = "0010_placement"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_courses_track_id",
        "courses",
        "language_tracks",
        ["track_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_courses_track_id", "courses", ["track_id"])

    op.create_table(
        "generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["language_tracks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_generation_jobs_track_id", "generation_jobs", ["track_id"])
    op.create_index("ix_generation_jobs_user_id", "generation_jobs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_generation_jobs_user_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_track_id", table_name="generation_jobs")
    op.drop_table("generation_jobs")
    op.drop_index("ix_courses_track_id", table_name="courses")
    op.drop_constraint("fk_courses_track_id", "courses", type_="foreignkey")
    op.drop_column("courses", "track_id")
