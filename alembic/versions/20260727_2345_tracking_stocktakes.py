"""tracking and stocktakes

Revision ID: 20260727_2345
Revises: 20260727_2305
Create Date: 2026-07-27 23:45:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_2345"
down_revision = "20260727_2305"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_stocktake_sessions",
        sa.Column("session_number", sa.String(length=50), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["asset_locations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_number"),
    )

    op.create_table(
        "asset_scan_events",
        sa.Column("event_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_tag_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("raw_tag_uid", sa.String(length=255), nullable=False),
        sa.Column("scan_type", sa.String(length=30), nullable=False),
        sa.Column("scan_source", sa.String(length=30), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scanned_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("gps_accuracy_meters", sa.Numeric(10, 2), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scanned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stocktake_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("match_status", sa.String(length=30), nullable=False),
        sa.Column("processing_status", sa.String(length=20), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["scanned_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["stocktake_session_id"],
            ["asset_stocktake_sessions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["transfer_id"], ["asset_transfers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_uid", name="uq_asset_scan_events_event_uid"),
    )

    op.create_table(
        "asset_verifications",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scan_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expected_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verification_result", sa.String(length=30), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolution_status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_action", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["expected_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["observed_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["scan_event_id"], ["asset_scan_events.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "asset_stocktake_expected_items",
        sa.Column("stocktake_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expected_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expected_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_status", sa.String(length=30), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["expected_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["stocktake_session_id"],
            ["asset_stocktake_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stocktake_session_id",
            "asset_id",
            name="uq_stocktake_expected_session_asset",
        ),
    )

    op.create_table(
        "asset_stocktake_results",
        sa.Column("stocktake_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scan_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_type", sa.String(length=30), nullable=False),
        sa.Column("observed_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("resolution_reference_type", sa.String(length=30), nullable=True),
        sa.Column("resolution_reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["observed_location_id"],
            ["asset_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["scan_event_id"], ["asset_scan_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["stocktake_session_id"],
            ["asset_stocktake_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stocktake_session_id",
            "asset_id",
            "result_type",
            name="uq_stocktake_result_session_asset_type",
        ),
    )

    op.create_index("ix_scan_asset_time", "asset_scan_events", ["asset_id", "scanned_at"])
    op.create_index(
        "ix_scan_location_time",
        "asset_scan_events",
        ["scanned_location_id", "scanned_at"],
    )
    op.create_index("ix_scan_tag_time", "asset_scan_events", ["raw_tag_uid", "scanned_at"])


def downgrade() -> None:
    op.drop_index("ix_scan_tag_time", table_name="asset_scan_events")
    op.drop_index("ix_scan_location_time", table_name="asset_scan_events")
    op.drop_index("ix_scan_asset_time", table_name="asset_scan_events")
    op.drop_table("asset_stocktake_results")
    op.drop_table("asset_stocktake_expected_items")
    op.drop_table("asset_verifications")
    op.drop_table("asset_scan_events")
    op.drop_table("asset_stocktake_sessions")
