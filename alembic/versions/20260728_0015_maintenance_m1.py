"""maintenance m1

Revision ID: 20260728_0015
Revises: 20260727_2345
Create Date: 2026-07-28 00:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0015"
down_revision = "20260727_2345"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_priorities",
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("severity_level", sa.Integer(), nullable=False),
        sa.Column("default_response_minutes", sa.Integer(), nullable=True),
        sa.Column("default_resolution_minutes", sa.Integer(), nullable=True),
        sa.Column("escalation_after_minutes", sa.Integer(), nullable=True),
        sa.Column("color_code", sa.String(length=20), nullable=True),
        sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "maintenance_requests",
        sa.Column("request_number", sa.String(length=50), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_type", sa.String(length=30), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("requested_by_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reported_by_name", sa.String(length=150), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("problem_description", sa.Text(), nullable=False),
        sa.Column("priority_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operating_condition", sa.Text(), nullable=True),
        sa.Column(
            "is_asset_stopped",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("downtime_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "safety_impact",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "environmental_impact",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "production_impact",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warranty_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_vendor_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("triaged_by_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("required_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("required_resolution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["asset_location_id"],
            ["asset_locations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_request_id"],
            ["maintenance_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["priority_id"],
            ["maintenance_priorities.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_vendor_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_number"),
    )

    op.create_table(
        "maintenance_work_orders",
        sa.Column("work_order_number", sa.String(length=50), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_type", sa.String(length=30), nullable=False),
        sa.Column("priority_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("scope_of_work", sa.Text(), nullable=False),
        sa.Column("maintenance_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_technician_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execution_mode", sa.String(length=20), nullable=False),
        sa.Column("vendor_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warranty_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asset_condition_before", sa.String(length=30), nullable=True),
        sa.Column("asset_condition_after", sa.String(length=30), nullable=True),
        sa.Column("completion_summary", sa.Text(), nullable=True),
        sa.Column("resolution_code", sa.String(length=30), nullable=True),
        sa.Column(
            "requires_shutdown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "requires_permit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "requires_verification",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_labor_cost", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("estimated_part_cost", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("estimated_vendor_cost", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("actual_labor_cost", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("actual_part_cost", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("actual_vendor_cost", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["priority_id"],
            ["maintenance_priorities.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["vendor_partner_id"],
            ["business_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("work_order_number"),
    )

    op.create_table(
        "maintenance_request_work_orders",
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=30), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "maintenance_request_id",
            "work_order_id",
            name="uq_maintenance_request_work_orders_request_work_order",
        ),
    )

    op.create_table(
        "maintenance_work_order_assignments",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_role", sa.String(length=30), nullable=False),
        sa.Column("planned_minutes", sa.Integer(), nullable=True),
        sa.Column("actual_minutes", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "work_order_id",
            "employee_id",
            "assignment_role",
            name="uq_maintenance_work_order_assignments_unique",
        ),
    )


def downgrade() -> None:
    op.drop_table("maintenance_work_order_assignments")
    op.drop_table("maintenance_request_work_orders")
    op.drop_table("maintenance_work_orders")
    op.drop_table("maintenance_requests")
    op.drop_table("maintenance_priorities")
