"""Create blogs table.

Revision ID: 002
Revises: 001
Create Date: 2026-11-19 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blogs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=280), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.String(length=1000), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blogs_slug"), "blogs", ["slug"], unique=True)
    op.create_index(op.f("ix_blogs_is_published"), "blogs", ["is_published"], unique=False)
    op.create_index(op.f("ix_blogs_published_at"), "blogs", ["published_at"], unique=False)
    op.create_index(op.f("ix_blogs_author_id"), "blogs", ["author_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_blogs_author_id"), table_name="blogs")
    op.drop_index(op.f("ix_blogs_published_at"), table_name="blogs")
    op.drop_index(op.f("ix_blogs_is_published"), table_name="blogs")
    op.drop_index(op.f("ix_blogs_slug"), table_name="blogs")
    op.drop_table("blogs")
