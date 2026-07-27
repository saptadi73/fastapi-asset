"""maintenance parts and labor logs

Revision ID: 20260728_0415
Revises: 20260728_0315
Create Date: 2026-07-28 04:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0415"
down_revision = "20260728_0315"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_part_usages",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("part_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(20, 4), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("usage_type", sa.String(length=20), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_by_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sap_inventory_doc_entry", sa.Integer(), nullable=True),
        sa.Column("sap_inventory_doc_num", sa.Integer(), nullable=True),
        sa.Column("removed_component_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("installed_component_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "maintenance_labor_logs",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("activity_type", sa.String(length=30), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(20, 4), nullable=True),
        sa.Column("labor_cost", sa.Numeric(20, 4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("maintenance_labor_logs")
    op.drop_table("maintenance_part_usages")
