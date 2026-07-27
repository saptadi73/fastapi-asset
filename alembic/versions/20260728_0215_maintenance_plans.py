"""maintenance plans

Revision ID: 20260728_0215
Revises: 20260728_0115
Create Date: 2026-07-28 02:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0215"
down_revision = "20260728_0115"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_plans",
        sa.Column("plan_code", sa.String(length=50), nullable=False),
        sa.Column("plan_name", sa.String(length=200), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_type", sa.String(length=30), nullable=False),
        sa.Column("trigger_type", sa.String(length=30), nullable=False),
        sa.Column("calendar_interval_value", sa.Integer(), nullable=True),
        sa.Column("calendar_interval_unit", sa.String(length=20), nullable=True),
        sa.Column("meter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meter_interval", sa.Numeric(20, 4), nullable=True),
        sa.Column("condition_rule", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("default_priority_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("default_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_vendor_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checklist_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "auto_create_request",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "auto_create_work_order",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column("next_due_meter_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_category_id"],
            ["asset_categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["default_priority_id"],
            ["maintenance_priorities.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["default_team_id"], ["maintenance_teams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["default_vendor_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_code"),
    )

    op.create_table(
        "maintenance_plan_assets",
        sa.Column("maintenance_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("override_interval_value", sa.Integer(), nullable=True),
        sa.Column("override_interval_unit", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_plan_id"],
            ["maintenance_plans.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "maintenance_plan_id",
            "asset_id",
            "effective_from",
            name="uq_maintenance_plan_assets_plan_asset_from",
        ),
    )

    op.create_index(
        "ix_maintenance_plan_assets_plan_active",
        "maintenance_plan_assets",
        ["maintenance_plan_id", "is_active", "effective_from"],
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_plan_assets_plan_active", table_name="maintenance_plan_assets")
    op.drop_table("maintenance_plan_assets")
    op.drop_table("maintenance_plans")
