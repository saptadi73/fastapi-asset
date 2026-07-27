"""maintenance sla snapshots

Revision ID: 20260728_0620
Revises: 20260728_0610
Create Date: 2026-07-28 06:20:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0620"
down_revision = "20260728_0610"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_sla_snapshots",
        sa.Column("maintenance_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("priority_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("response_target_minutes", sa.Integer(), nullable=True),
        sa.Column("resolution_target_minutes", sa.Integer(), nullable=True),
        sa.Column("response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "response_breached",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "resolution_breached",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("snapshot_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["priority_id"],
            ["maintenance_priorities.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("maintenance_sla_snapshots")
