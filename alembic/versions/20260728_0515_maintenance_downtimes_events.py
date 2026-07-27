"""maintenance downtimes and work order events

Revision ID: 20260728_0515
Revises: 20260728_0415
Create Date: 2026-07-28 05:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0515"
down_revision = "20260728_0415"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_downtimes",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("downtime_type", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("production_loss_quantity", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit_of_measure", sa.String(length=20), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "maintenance_work_order_events",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=True),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("maintenance_work_order_events")
    op.drop_table("maintenance_downtimes")
