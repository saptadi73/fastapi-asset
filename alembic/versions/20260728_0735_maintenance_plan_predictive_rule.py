"""maintenance plan predictive rule

Revision ID: 20260728_0735
Revises: 20260728_0725
Create Date: 2026-07-28 07:35:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260728_0735"
down_revision = "20260728_0725"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "maintenance_plans",
        sa.Column(
            "predictive_rule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("maintenance_plans", "predictive_rule")
