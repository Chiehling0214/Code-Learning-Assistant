"""initial schema: users, student_profiles, programming_languages, courses

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("firebase_uid", name="uq_users_firebase_uid"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_level", sa.String(length=32), nullable=False, server_default="beginner"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
    )

    op.create_table(
        "programming_languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_programming_languages_name"),
        sa.UniqueConstraint("slug", name="uq_programming_languages_slug"),
    )
    op.create_index("ix_programming_languages_slug", "programming_languages", ["slug"])

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("language_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["language_id"], ["programming_languages.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug", name="uq_courses_slug"),
    )
    op.create_index("ix_courses_slug", "courses", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_courses_slug", table_name="courses")
    op.drop_table("courses")
    op.drop_index("ix_programming_languages_slug", table_name="programming_languages")
    op.drop_table("programming_languages")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_table("users")
