"""asset lifecycle reviews and retirements

Revision ID: 20260728_0630
Revises: 20260728_0620
Create Date: 2026-07-28 06:30:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0630"
down_revision = "20260728_0620"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("expected_replacement_date", sa.Date(), nullable=True))
    op.add_column("assets", sa.Column("support_end_date", sa.Date(), nullable=True))
    op.add_column("assets", sa.Column("vendor_end_of_sale_date", sa.Date(), nullable=True))
    op.add_column("assets", sa.Column("vendor_end_of_support_date", sa.Date(), nullable=True))
    op.add_column("assets", sa.Column("replacement_strategy", sa.String(length=30), nullable=True))
    op.add_column("assets", sa.Column("replacement_priority", sa.String(length=20), nullable=True))
    op.add_column(
        "assets",
        sa.Column("estimated_replacement_cost", sa.Numeric(20, 4), nullable=True),
    )
    op.add_column("assets", sa.Column("replacement_budget_year", sa.Integer(), nullable=True))
    op.add_column("assets", sa.Column("next_review_date", sa.Date(), nullable=True))

    op.create_table(
        "asset_lifecycle_reviews",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("condition_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("remaining_life_months", sa.Integer(), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("replacement_recommendation", sa.String(length=30), nullable=False),
        sa.Column("estimated_replacement_cost", sa.Numeric(20, 4), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "condition_score >= 0 AND condition_score <= 100",
            name="ck_asset_lifecycle_reviews_condition_score",
        ),
        sa.CheckConstraint(
            "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)",
            name="ck_asset_lifecycle_reviews_risk_score",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id",
            "review_date",
            name="uq_asset_lifecycle_reviews_asset_date",
        ),
    )

    op.create_table(
        "asset_retirements",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("retirement_number", sa.String(length=50), nullable=False),
        sa.Column("retirement_type", sa.String(length=30), nullable=False),
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "proceeds_amount",
            sa.Numeric(20, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("buyer_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sap_retirement_doc_entry", sa.Integer(), nullable=True),
        sa.Column("sap_trans_id", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "effective_date IS NULL OR effective_date >= request_date",
            name="ck_asset_retirements_effective_after_request",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["buyer_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("retirement_number", name="uq_asset_retirements_number"),
    )
    op.create_index(
        "ix_asset_retirements_asset_status",
        "asset_retirements",
        ["asset_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_asset_retirements_asset_status", table_name="asset_retirements")
    op.drop_table("asset_retirements")
    op.drop_table("asset_lifecycle_reviews")
    op.drop_column("assets", "next_review_date")
    op.drop_column("assets", "replacement_budget_year")
    op.drop_column("assets", "estimated_replacement_cost")
    op.drop_column("assets", "replacement_priority")
    op.drop_column("assets", "replacement_strategy")
    op.drop_column("assets", "vendor_end_of_support_date")
    op.drop_column("assets", "vendor_end_of_sale_date")
    op.drop_column("assets", "support_end_date")
    op.drop_column("assets", "expected_replacement_date")
