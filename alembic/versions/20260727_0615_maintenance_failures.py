"""maintenance failures and root cause masters

Revision ID: 20260727_0615
Revises: 20260728_0515
Create Date: 2026-07-27 06:15:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_0615"
down_revision = "20260728_0515"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_symptom_codes",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "maintenance_failure_modes",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "maintenance_root_cause_codes",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "asset_failures",
        sa.Column("failure_number", sa.String(length=50), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_by_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("failure_mode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("symptom_code_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("failure_description", sa.Text(), nullable=False),
        sa.Column("failure_severity", sa.String(length=20), nullable=False),
        sa.Column("asset_condition_before", sa.String(length=30), nullable=True),
        sa.Column("asset_condition_after", sa.String(length=30), nullable=True),
        sa.Column(
            "caused_shutdown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "safety_incident",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "repeat_failure",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("temporary_action", sa.Text(), nullable=True),
        sa.Column("root_cause_code_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("root_cause_description", sa.Text(), nullable=True),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("preventive_action", sa.Text(), nullable=True),
        sa.Column("failure_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downtime_minutes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["failure_mode_id"],
            ["maintenance_failure_modes.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["root_cause_code_id"],
            ["maintenance_root_cause_codes.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["symptom_code_id"],
            ["maintenance_symptom_codes.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("failure_number"),
    )


def downgrade() -> None:
    op.drop_table("asset_failures")
    op.drop_table("maintenance_root_cause_codes")
    op.drop_table("maintenance_failure_modes")
    op.drop_table("maintenance_symptom_codes")
