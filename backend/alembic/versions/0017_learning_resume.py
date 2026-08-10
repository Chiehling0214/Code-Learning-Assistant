"""Persist the learner's latest course item for precise resume.

Revision ID: 0017_learning_resume
Revises: 0016_course_kind
Create Date: 2026-08-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_learning_resume"
down_revision: str | None = "0016_course_kind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("last_course_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "student_profiles", sa.Column("last_item_type", sa.String(length=16), nullable=True)
    )
    op.add_column(
        "student_profiles",
        sa.Column("last_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "student_profiles",
        sa.Column("last_learning_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_student_profiles_last_course_id",
        "student_profiles",
        "courses",
        ["last_course_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_student_profiles_last_course_id", "student_profiles", type_="foreignkey"
    )
    op.drop_column("student_profiles", "last_learning_at")
    op.drop_column("student_profiles", "last_item_id")
    op.drop_column("student_profiles", "last_item_type")
    op.drop_column("student_profiles", "last_course_id")
