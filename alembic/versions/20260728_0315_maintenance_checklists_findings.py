"""maintenance checklists and findings

Revision ID: 20260728_0315
Revises: 20260728_0215
Create Date: 2026-07-28 03:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0315"
down_revision = "20260728_0215"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_checklist_templates",
        sa.Column("template_code", sa.String(length=50), nullable=False),
        sa.Column("template_name", sa.String(length=200), nullable=False),
        sa.Column("asset_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_type", sa.String(length=30), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_category_id"],
            ["asset_categories.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_code"),
    )

    op.create_table(
        "maintenance_checklist_template_items",
        sa.Column("checklist_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=50), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("response_type", sa.String(length=30), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("normal_min_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("normal_max_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit_of_measure", sa.String(length=20), nullable=True),
        sa.Column("failure_response_rule", sa.String(length=30), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["checklist_template_id"],
            ["maintenance_checklist_templates.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "checklist_template_id",
            "sequence_no",
            name="uq_maintenance_checklist_template_items_template_sequence",
        ),
    )

    op.create_table(
        "maintenance_checklist_executions",
        sa.Column("checklist_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("maintenance_schedule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("performed_by_employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overall_result", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["checklist_template_id"],
            ["maintenance_checklist_templates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_schedule_id"],
            ["maintenance_schedules.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "maintenance_checklist_results",
        sa.Column("checklist_execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result_status", sa.String(length=20), nullable=True),
        sa.Column("boolean_value", sa.Boolean(), nullable=True),
        sa.Column("numeric_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("meter_reading_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["checklist_execution_id"],
            ["maintenance_checklist_executions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["template_item_id"],
            ["maintenance_checklist_template_items.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "checklist_execution_id",
            "template_item_id",
            name="uq_maintenance_checklist_results_execution_template_item",
        ),
    )

    op.create_table(
        "maintenance_findings",
        sa.Column("finding_number", sa.String(length=50), nullable=False),
        sa.Column("checklist_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column(
            "requires_follow_up",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "requires_asset_shutdown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("follow_up_due_date", sa.Date(), nullable=True),
        sa.Column("generated_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reported_by_employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["checklist_result_id"],
            ["maintenance_checklist_results.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["generated_request_id"],
            ["maintenance_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_number"),
    )


def downgrade() -> None:
    op.drop_table("maintenance_findings")
    op.drop_table("maintenance_checklist_results")
    op.drop_table("maintenance_checklist_executions")
    op.drop_table("maintenance_checklist_template_items")
    op.drop_table("maintenance_checklist_templates")
