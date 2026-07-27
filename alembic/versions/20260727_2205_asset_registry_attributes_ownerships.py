"""asset registry attributes ownerships

Revision ID: 20260727_2205
Revises: 20260727_2140
Create Date: 2026-07-27 22:05:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_2205"
down_revision = "20260727_2140"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_attribute_definitions",
        sa.Column("asset_category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attribute_code", sa.String(length=50), nullable=False),
        sa.Column("attribute_name", sa.String(length=150), nullable=False),
        sa.Column("data_type", sa.String(length=20), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=30), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("validation_rule", sa.JSON(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_category_id"],
            ["asset_categories.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_category_id",
            "attribute_code",
            name="uq_asset_attribute_definitions_category_code",
        ),
    )

    op.create_table(
        "asset_attribute_values",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attribute_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Numeric(20, 6), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_definition_id"],
            ["asset_attribute_definitions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id",
            "attribute_definition_id",
            name="uq_asset_attribute_values_asset_definition",
        ),
    )

    op.create_table(
        "asset_ownerships",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_type", sa.String(length=30), nullable=False),
        sa.Column("owner_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ownership_percentage", sa.Numeric(8, 4), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("source_reference", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "ownership_percentage > 0 AND ownership_percentage <= 100",
            name="ck_asset_ownerships_percentage_range",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_asset_ownerships_effective_period",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_asset_attribute_values_asset",
        "asset_attribute_values",
        ["asset_id"],
    )
    op.create_index(
        "ix_asset_ownerships_asset_effective_from",
        "asset_ownerships",
        ["asset_id", "effective_from"],
    )


def downgrade() -> None:
    op.drop_index("ix_asset_ownerships_asset_effective_from", table_name="asset_ownerships")
    op.drop_index("ix_asset_attribute_values_asset", table_name="asset_attribute_values")
    op.drop_table("asset_ownerships")
    op.drop_table("asset_attribute_values")
    op.drop_table("asset_attribute_definitions")
