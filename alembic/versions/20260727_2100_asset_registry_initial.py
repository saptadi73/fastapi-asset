"""asset registry initial

Revision ID: 20260727_2100
Revises:
Create Date: 2026-07-27 21:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_2100"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_categories",
        sa.Column("category_code", sa.String(length=50), nullable=False),
        sa.Column("category_name", sa.String(length=150), nullable=False),
        sa.Column("parent_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_code"),
        sa.ForeignKeyConstraint(
            ["parent_category_id"],
            ["asset_categories.id"],
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "asset_classes",
        sa.Column("class_code", sa.String(length=50), nullable=False),
        sa.Column("class_name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sap_asset_class_code", sa.String(length=50), nullable=True),
        sa.Column("default_useful_life_months", sa.Integer(), nullable=True),
        sa.Column("is_depreciable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_code"),
    )

    op.create_table(
        "business_partners",
        sa.Column("partner_code", sa.String(length=50), nullable=False),
        sa.Column("partner_name", sa.String(length=200), nullable=False),
        sa.Column("tax_number", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("sap_card_code", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_code"),
    )

    op.create_table(
        "business_partner_roles",
        sa.Column("business_partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_type", sa.String(length=30), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_partner_id"],
            ["business_partners.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_partner_id",
            "role_type",
            "valid_from",
            name="uq_business_partner_role_valid_from",
        ),
    )

    op.create_table(
        "assets",
        sa.Column("asset_code", sa.String(length=50), nullable=False),
        sa.Column("asset_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("asset_category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_class_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parent_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_type", sa.String(length=30), nullable=False),
        sa.Column("asset_status", sa.String(length=30), nullable=False),
        sa.Column("condition_status", sa.String(length=30), nullable=False),
        sa.Column("criticality_level", sa.String(length=20), nullable=True),
        sa.Column("serial_number", sa.String(length=150), nullable=True),
        sa.Column("manufacturer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("manufacture_year", sa.Integer(), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_primary_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("barcode", sa.String(length=100), nullable=True),
        sa.Column("qr_code", sa.String(length=200), nullable=True),
        sa.Column("tag_number", sa.String(length=100), nullable=True),
        sa.Column(
            "tracking_status",
            sa.String(length=20),
            nullable=False,
            server_default="TRACKED",
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("in_service_date", sa.Date(), nullable=True),
        sa.Column("retirement_date", sa.Date(), nullable=True),
        sa.Column("sap_asset_code", sa.String(length=50), nullable=True),
        sa.Column("sap_item_code", sa.String(length=50), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "parent_asset_id IS NULL OR parent_asset_id <> id",
            name="ck_assets_no_self_parent",
        ),
        sa.CheckConstraint(
            "manufacture_year IS NULL OR manufacture_year BETWEEN 1900 AND 2200",
            name="ck_assets_manufacture_year",
        ),
        sa.CheckConstraint(
            (
                "retirement_date IS NULL OR in_service_date IS NULL "
                "OR retirement_date >= in_service_date"
            ),
            name="ck_assets_retirement_after_service",
        ),
        sa.ForeignKeyConstraint(
            ["asset_category_id"],
            ["asset_categories.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["asset_class_id"], ["asset_classes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["manufacturer_id"], ["business_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_code"),
    )

    op.create_index("ix_assets_status", "assets", ["company_id", "asset_status"])
    op.create_index("ix_assets_serial_number", "assets", ["serial_number"])


def downgrade() -> None:
    op.drop_index("ix_assets_serial_number", table_name="assets")
    op.drop_index("ix_assets_status", table_name="assets")
    op.drop_table("assets")
    op.drop_table("business_partner_roles")
    op.drop_table("business_partners")
    op.drop_table("asset_classes")
    op.drop_table("asset_categories")
