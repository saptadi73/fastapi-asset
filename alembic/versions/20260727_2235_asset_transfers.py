"""asset transfers

Revision ID: 20260727_2235
Revises: 20260727_2205
Create Date: 2026-07-27 22:35:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_2235"
down_revision = "20260727_2205"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_transfers",
        sa.Column("transfer_number", sa.String(length=50), nullable=False),
        sa.Column("transfer_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transfer_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("movement_purpose", sa.String(length=30), nullable=False),
        sa.Column("is_permanent", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("expected_return_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("from_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispatched_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.UniqueConstraint("transfer_number"),
    )

    op.create_table(
        "asset_transfer_items",
        sa.Column("asset_transfer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("new_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("handover_condition", sa.String(length=30), nullable=False),
        sa.Column("dispatch_scan_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("receipt_scan_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_transfer_id"],
            ["asset_transfers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_transfer_id",
            "asset_id",
            name="uq_asset_transfer_items_transfer_asset",
        ),
    )

    op.create_index("ix_asset_transfers_status", "asset_transfers", ["status"])
    op.create_index(
        "ix_asset_transfer_items_transfer",
        "asset_transfer_items",
        ["asset_transfer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_asset_transfer_items_transfer", table_name="asset_transfer_items")
    op.drop_index("ix_asset_transfers_status", table_name="asset_transfers")
    op.drop_table("asset_transfer_items")
    op.drop_table("asset_transfers")
