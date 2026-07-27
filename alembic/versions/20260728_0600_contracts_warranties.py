"""maintenance contracts and asset warranties

Revision ID: 20260728_0600
Revises: 20260728_0515
Create Date: 2026-07-28 06:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0600"
down_revision = "20260728_0515"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_contracts",
        sa.Column("contract_number", sa.String(length=100), nullable=False),
        sa.Column("contract_name", sa.String(length=200), nullable=False),
        sa.Column("vendor_partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contract_type", sa.String(length=30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("response_time_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("resolution_time_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("preventive_maintenance_included", sa.Boolean(), nullable=False),
        sa.Column("corrective_maintenance_included", sa.Boolean(), nullable=False),
        sa.Column("spare_parts_included", sa.Boolean(), nullable=False),
        sa.Column("labor_included", sa.Boolean(), nullable=False),
        sa.Column("onsite_support_included", sa.Boolean(), nullable=False),
        sa.Column("remote_support_included", sa.Boolean(), nullable=False),
        sa.Column("contract_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("billing_frequency", sa.String(length=20), nullable=True),
        sa.Column("auto_renewal", sa.Boolean(), nullable=False),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sap_purchase_contract_reference", sa.String(length=100), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["vendor_partner_id"],
            ["business_partners.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_number"),
    )

    op.create_table(
        "maintenance_contract_assets",
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("coverage_start_date", sa.Date(), nullable=False),
        sa.Column("coverage_end_date", sa.Date(), nullable=False),
        sa.Column("coverage_level", sa.String(length=30), nullable=False),
        sa.Column("annual_allocation_amount", sa.Numeric(20, 4), nullable=True),
        sa.Column("specific_exclusions", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_contract_id"],
            ["maintenance_contracts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "maintenance_contract_id",
            "asset_id",
            "coverage_start_date",
            name="uq_maintenance_contract_assets_contract_asset_start",
        ),
    )

    op.create_table(
        "asset_warranties",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warranty_provider_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warranty_type", sa.String(length=30), nullable=False),
        sa.Column("warranty_number", sa.String(length=100), nullable=True),
        sa.Column("coverage_start_date", sa.Date(), nullable=False),
        sa.Column("coverage_end_date", sa.Date(), nullable=False),
        sa.Column("claim_deadline_date", sa.Date(), nullable=True),
        sa.Column("coverage_scope", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["warranty_provider_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("asset_warranties")
    op.drop_table("maintenance_contract_assets")
    op.drop_table("maintenance_contracts")
