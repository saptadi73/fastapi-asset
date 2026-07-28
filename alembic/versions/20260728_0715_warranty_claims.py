"""warranty claims

Revision ID: 20260728_0715
Revises: 20260728_0700
Create Date: 2026-07-28 07:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0715"
down_revision = "20260728_0700"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_warranty_claims",
        sa.Column("warranty_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_number", sa.String(length=100), nullable=False),
        sa.Column("claim_date", sa.Date(), nullable=False),
        sa.Column("problem_description", sa.Text(), nullable=False),
        sa.Column("claim_status", sa.String(length=30), nullable=False),
        sa.Column("resolution_description", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replacement_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cost_covered", sa.Numeric(20, 4), nullable=True),
        sa.Column("cost_not_covered", sa.Numeric(20, 4), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["replacement_asset_id"],
            ["assets.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["warranty_id"],
            ["asset_warranties.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_number"),
    )
    op.create_index(
        "ix_asset_warranty_claims_warranty_claim_date",
        "asset_warranty_claims",
        ["warranty_id", "claim_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_asset_warranty_claims_warranty_claim_date",
        table_name="asset_warranty_claims",
    )
    op.drop_table("asset_warranty_claims")
