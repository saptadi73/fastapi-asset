"""attachment file events

Revision ID: 20260728_0700
Revises: 20260728_0650
Create Date: 2026-07-28 07:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0700"
down_revision = "20260728_0650"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "file_events",
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attachment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["attachment_id"],
            ["attachments.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["file_version_id"],
            ["file_versions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_file_events_attachment_occurred_at",
        "file_events",
        ["attachment_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_file_events_attachment_occurred_at", table_name="file_events")
    op.drop_table("file_events")
