"""asset registry histories

Revision ID: 20260727_2140
Revises: 20260727_2100
Create Date: 2026-07-27 21:40:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_2140"
down_revision = "20260727_2100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_locations",
        sa.Column("location_code", sa.String(length=50), nullable=False),
        sa.Column("location_name", sa.String(length=150), nullable=False),
        sa.Column("location_type", sa.String(length=30), nullable=False),
        sa.Column("parent_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warehouse_code", sa.String(length=50), nullable=True),
        sa.Column("bin_location_code", sa.String(length=50), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_code"),
    )

    op.create_table(
        "asset_location_histories",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["from_location_id"],
            ["asset_locations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["to_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "asset_assignments",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_type", sa.String(length=30), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_return_date", sa.Date(), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handover_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accepted_by_employee_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by_employee_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assignment_status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "returned_at IS NULL OR returned_at >= assigned_at",
            name="ck_asset_assignments_returned_after_assigned",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "asset_id", name="uq_asset_assignments_id_asset"),
    )

    op.create_table(
        "asset_status_histories",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=False),
        sa.Column("previous_condition", sa.String(length=30), nullable=True),
        sa.Column("new_condition", sa.String(length=30), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_asset_assignments_asset_type",
        "asset_assignments",
        ["asset_id", "assignment_type"],
    )
    op.create_index(
        "ix_asset_location_histories_asset_effective",
        "asset_location_histories",
        ["asset_id", "effective_at"],
    )
    op.create_index(
        "ix_asset_status_histories_asset_effective",
        "asset_status_histories",
        ["asset_id", "effective_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_asset_status_histories_asset_effective",
        table_name="asset_status_histories",
    )
    op.drop_index(
        "ix_asset_location_histories_asset_effective",
        table_name="asset_location_histories",
    )
    op.drop_index("ix_asset_assignments_asset_type", table_name="asset_assignments")
    op.drop_table("asset_status_histories")
    op.drop_table("asset_assignments")
    op.drop_table("asset_location_histories")
    op.drop_table("asset_locations")
