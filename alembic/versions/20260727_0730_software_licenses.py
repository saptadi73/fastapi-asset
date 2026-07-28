"""software licenses

Revision ID: 20260727_0730
Revises: 20260727_0720
Create Date: 2026-07-27 07:30:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_0730"
down_revision = "20260727_0720"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "software_products",
        sa.Column("product_code", sa.String(length=50), nullable=False),
        sa.Column("product_name", sa.String(length=150), nullable=False),
        sa.Column("publisher_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("publisher_name", sa.String(length=150), nullable=True),
        sa.Column("product_type", sa.String(length=30), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("edition", sa.String(length=100), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["publisher_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_code"),
    )
    op.create_table(
        "software_licenses",
        sa.Column("software_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_number", sa.String(length=150), nullable=True),
        sa.Column("license_key_encrypted", sa.Text(), nullable=True),
        sa.Column("license_model", sa.String(length=30), nullable=False),
        sa.Column("license_metric", sa.String(length=30), nullable=False),
        sa.Column("license_quantity", sa.Integer(), nullable=False),
        sa.Column(
            "used_quantity",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("activation_date", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("renewal_type", sa.String(length=30), nullable=True),
        sa.Column(
            "auto_renewal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "renewal_notice_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("30"),
        ),
        sa.Column("subscription_cost", sa.Numeric(20, 4), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("support_end_date", sa.Date(), nullable=True),
        sa.Column("update_entitlement_end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "expiry_date IS NULL OR start_date IS NULL OR expiry_date >= start_date",
            name="ck_software_licenses_expiry_after_start",
        ),
        sa.CheckConstraint(
            "license_quantity >= 0",
            name="ck_software_licenses_quantity_non_negative",
        ),
        sa.CheckConstraint(
            "used_quantity <= license_quantity",
            name="ck_software_licenses_used_not_exceed_quantity",
        ),
        sa.CheckConstraint(
            "used_quantity >= 0",
            name="ck_software_licenses_used_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["software_product_id"],
            ["software_products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "software_license_assignments",
        sa.Column("software_license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assignment_type", sa.String(length=30), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "(asset_id IS NOT NULL AND employee_id IS NULL) OR "
            "(asset_id IS NULL AND employee_id IS NOT NULL)",
            name="ck_software_license_assignments_target_choice",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["software_license_id"],
            ["software_licenses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "software_license_id",
            "asset_id",
            "employee_id",
            "assigned_at",
            name="uq_software_license_assignments_unique",
        ),
    )
    op.create_index(
        "ix_software_licenses_expiry_date",
        "software_licenses",
        ["expiry_date"],
    )
    op.create_index(
        "ix_software_license_assignments_license_active",
        "software_license_assignments",
        ["software_license_id", "released_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_software_license_assignments_license_active",
        table_name="software_license_assignments",
    )
    op.drop_index(
        "ix_software_licenses_expiry_date",
        table_name="software_licenses",
    )
    op.drop_table("software_license_assignments")
    op.drop_table("software_licenses")
    op.drop_table("software_products")
