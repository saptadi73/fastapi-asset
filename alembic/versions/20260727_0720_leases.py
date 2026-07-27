"""leases

Revision ID: 20260727_0720
Revises: 20260727_0710
Create Date: 2026-07-27 07:20:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_0720"
down_revision = "20260727_0710"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_lease_contracts",
        sa.Column("contract_number", sa.String(length=100), nullable=False),
        sa.Column("lessor_partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lessee_company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lease_type", sa.String(length=30), nullable=False),
        sa.Column("accounting_treatment", sa.String(length=30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("extension_option_end_date", sa.Date(), nullable=True),
        sa.Column("billing_frequency", sa.String(length=20), nullable=False),
        sa.Column("payment_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column(
            "deposit_amount",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("purchase_option_amount", sa.Numeric(20, 4), nullable=True),
        sa.Column(
            "auto_renewal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column(
            "maintenance_included",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "insurance_included",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "tax_included",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("end_date >= start_date", name="ck_asset_lease_contracts_period"),
        sa.ForeignKeyConstraint(
            ["lessor_partner_id"],
            ["business_partners.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_number"),
    )
    op.create_table(
        "asset_lease_items",
        sa.Column("lease_contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lease_start_date", sa.Date(), nullable=False),
        sa.Column("lease_end_date", sa.Date(), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(20, 4), nullable=True),
        sa.Column(
            "allocation_percentage",
            sa.Numeric(8, 4),
            nullable=False,
            server_default=sa.text("100"),
        ),
        sa.Column("return_condition", sa.Text(), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "allocation_percentage > 0 AND allocation_percentage <= 100",
            name="ck_asset_lease_items_allocation_range",
        ),
        sa.CheckConstraint(
            "lease_end_date >= lease_start_date",
            name="ck_asset_lease_items_period",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["lease_contract_id"],
            ["asset_lease_contracts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lease_contract_id",
            "asset_id",
            "lease_start_date",
            name="uq_asset_lease_items_contract_asset_start",
        ),
    )
    op.create_table(
        "asset_lease_payments",
        sa.Column("lease_contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "principal_amount",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "interest_amount",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "service_amount",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("total_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("payment_status", sa.String(length=20), nullable=False),
        sa.Column("sap_ap_invoice_doc_entry", sa.Integer(), nullable=True),
        sa.Column("sap_payment_doc_entry", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("period_end >= period_start", name="ck_asset_lease_payments_period"),
        sa.CheckConstraint(
            "total_amount >= 0",
            name="ck_asset_lease_payments_total_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["lease_contract_id"],
            ["asset_lease_contracts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lease_contract_id",
            "period_start",
            "period_end",
            name="uq_asset_lease_payments_contract_period",
        ),
    )
    op.create_index(
        "ix_asset_lease_items_asset_id",
        "asset_lease_items",
        ["asset_id"],
    )
    op.create_index(
        "ix_asset_lease_payments_lease_contract_id",
        "asset_lease_payments",
        ["lease_contract_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_asset_lease_payments_lease_contract_id",
        table_name="asset_lease_payments",
    )
    op.drop_index(
        "ix_asset_lease_items_asset_id",
        table_name="asset_lease_items",
    )
    op.drop_table("asset_lease_payments")
    op.drop_table("asset_lease_items")
    op.drop_table("asset_lease_contracts")
