"""maintenance schedule events

Revision ID: 20260728_0725
Revises: 20260728_0715
Create Date: 2026-07-28 07:25:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0725"
down_revision = "20260728_0715"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_schedule_events",
        sa.Column(
            "maintenance_schedule_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=True),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_schedule_id"],
            ["maintenance_schedules.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_schedule_events_schedule_event_at",
        "maintenance_schedule_events",
        ["maintenance_schedule_id", "event_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_schedule_events_schedule_event_at",
        table_name="maintenance_schedule_events",
    )
    op.drop_table("maintenance_schedule_events")
