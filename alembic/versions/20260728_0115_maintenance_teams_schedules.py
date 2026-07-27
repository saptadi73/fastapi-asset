"""maintenance teams and schedules

Revision ID: 20260728_0115
Revises: 20260728_0015
Create Date: 2026-07-28 01:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0115"
down_revision = "20260728_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_teams",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_code", sa.String(length=30), nullable=False),
        sa.Column("team_name", sa.String(length=150), nullable=False),
        sa.Column("team_type", sa.String(length=30), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supervisor_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["default_location_id"],
            ["asset_locations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "team_code", name="uq_maintenance_teams_company_code"),
    )

    op.create_table(
        "maintenance_team_members",
        sa.Column("maintenance_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_role", sa.String(length=30), nullable=False),
        sa.Column("skill_level", sa.String(length=20), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_team_id"],
            ["maintenance_teams.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "maintenance_team_id",
            "employee_id",
            "effective_from",
            name="uq_maintenance_team_members_team_employee_from",
        ),
    )

    op.create_table(
        "maintenance_schedules",
        sa.Column("schedule_number", sa.String(length=50), nullable=False),
        sa.Column("maintenance_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schedule_source", sa.String(length=30), nullable=False),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("maintenance_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vendor_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reschedule_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reschedule_reason", sa.Text(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_team_id"],
            ["maintenance_teams.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["vendor_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_number"),
    )

    op.create_index(
        "ix_maintenance_schedules_asset_window",
        "maintenance_schedules",
        ["asset_id", "scheduled_start_at", "scheduled_end_at"],
    )
    op.create_index(
        "ix_maintenance_schedules_team_window",
        "maintenance_schedules",
        ["maintenance_team_id", "scheduled_start_at", "scheduled_end_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_maintenance_schedules_team_window", table_name="maintenance_schedules")
    op.drop_index("ix_maintenance_schedules_asset_window", table_name="maintenance_schedules")
    op.drop_table("maintenance_schedules")
    op.drop_table("maintenance_team_members")
    op.drop_table("maintenance_teams")
