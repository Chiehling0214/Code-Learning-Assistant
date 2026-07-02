"""In-course chat messages (Sprint 12)

Revision ID: 0012_course_chat
Revises: 0011_curriculum
Create Date: 2026-07-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0012_course_chat"
down_revision: str | None = "0011_curriculum"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_course_chat_messages_course_id", "course_chat_messages", ["course_id"]
    )
    op.create_index(
        "ix_course_chat_messages_user_id", "course_chat_messages", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_course_chat_messages_user_id", table_name="course_chat_messages")
    op.drop_index("ix_course_chat_messages_course_id", table_name="course_chat_messages")
    op.drop_table("course_chat_messages")
