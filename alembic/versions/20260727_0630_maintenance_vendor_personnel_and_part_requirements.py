"""maintenance vendor personnel and part requirements

Revision ID: 20260727_0630
Revises: 20260728_0620
Create Date: 2026-07-27 06:30:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_0630"
down_revision = "20260728_0620"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_part_requirements",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("part_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("required_quantity", sa.Numeric(20, 4), nullable=False),
        sa.Column(
            "reserved_quantity",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "issued_quantity",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "returned_quantity",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("unit_of_measure", sa.String(length=20), nullable=False),
        sa.Column("requirement_status", sa.String(length=20), nullable=False),
        sa.Column(
            "is_critical",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "maintenance_vendor_personnel",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_name", sa.String(length=150), nullable=False),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("technician_reference", sa.String(length=100), nullable=True),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["vendor_partner_id"],
            ["business_partners.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_part_requirements_work_order_id",
        "maintenance_part_requirements",
        ["work_order_id"],
    )
    op.create_index(
        "ix_maintenance_part_requirements_work_order_part_item",
        "maintenance_part_requirements",
        ["work_order_id", "part_item_id"],
    )
    op.create_index(
        "ix_maintenance_vendor_personnel_work_order_id",
        "maintenance_vendor_personnel",
        ["work_order_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_vendor_personnel_work_order_id",
        table_name="maintenance_vendor_personnel",
    )
    op.drop_index(
        "ix_maintenance_part_requirements_work_order_part_item",
        table_name="maintenance_part_requirements",
    )
    op.drop_index(
        "ix_maintenance_part_requirements_work_order_id",
        table_name="maintenance_part_requirements",
    )
    op.drop_table("maintenance_vendor_personnel")
    op.drop_table("maintenance_part_requirements")
