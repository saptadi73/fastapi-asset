"""asset component histories

Revision ID: 20260728_0650
Revises: 20260728_0640
Create Date: 2026-07-28 06:50:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0650"
down_revision = "20260728_0640"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_component_histories",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column(
            "removed_component_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "installed_component_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "("
            "(action_type = 'INSTALL' AND installed_component_asset_id IS NOT NULL "
            "AND removed_component_asset_id IS NULL)"
            " OR "
            "(action_type = 'REMOVE' AND installed_component_asset_id IS NULL "
            "AND removed_component_asset_id IS NOT NULL)"
            " OR "
            "(action_type = 'REPLACE' AND installed_component_asset_id IS NOT NULL "
            "AND removed_component_asset_id IS NOT NULL)"
            ")",
            name="ck_asset_component_histories_action_targets",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["removed_component_asset_id"],
            ["assets.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["installed_component_asset_id"],
            ["assets.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_asset_component_histories_asset_effective_at",
        "asset_component_histories",
        ["asset_id", "effective_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_asset_component_histories_asset_effective_at",
        table_name="asset_component_histories",
    )
    op.drop_table("asset_component_histories")
