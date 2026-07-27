"""maintenance skills and required skills

Revision ID: 20260727_0710
Revises: 20260727_0630
Create Date: 2026-07-27 07:10:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_0710"
down_revision = "20260727_0630"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_skills",
        sa.Column("skill_code", sa.String(length=30), nullable=False),
        sa.Column("skill_name", sa.String(length=150), nullable=False),
        sa.Column(
            "certification_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_code"),
    )
    op.create_table(
        "employee_maintenance_skills",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proficiency_level", sa.String(length=20), nullable=True),
        sa.Column("certificate_number", sa.String(length=100), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_skill_id"],
            ["maintenance_skills.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id",
            "maintenance_skill_id",
            "valid_from",
            name="uq_employee_maintenance_skills_employee_skill_from",
        ),
    )
    op.create_table(
        "maintenance_work_order_required_skills",
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("maintenance_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("minimum_proficiency_level", sa.String(length=20), nullable=True),
        sa.Column(
            "certification_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_skill_id"],
            ["maintenance_skills.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["maintenance_work_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "work_order_id",
            "maintenance_skill_id",
            name="uq_maintenance_work_order_required_skills_unique",
        ),
    )
    op.create_index(
        "ix_employee_maintenance_skills_employee_id",
        "employee_maintenance_skills",
        ["employee_id"],
    )
    op.create_index(
        "ix_maintenance_work_order_required_skills_work_order_id",
        "maintenance_work_order_required_skills",
        ["work_order_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_work_order_required_skills_work_order_id",
        table_name="maintenance_work_order_required_skills",
    )
    op.drop_index(
        "ix_employee_maintenance_skills_employee_id",
        table_name="employee_maintenance_skills",
    )
    op.drop_table("maintenance_work_order_required_skills")
    op.drop_table("employee_maintenance_skills")
    op.drop_table("maintenance_skills")
