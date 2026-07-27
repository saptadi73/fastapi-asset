"""assets location foreign keys

Revision ID: 20260727_2245
Revises: 20260727_2235
Create Date: 2026-07-27 22:45:00
"""

from alembic import op

revision = "20260727_2245"
down_revision = "20260727_2235"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_assets_current_location_id_asset_locations",
        "assets",
        "asset_locations",
        ["current_location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_assets_last_verified_location_id_asset_locations",
        "assets",
        "asset_locations",
        ["last_verified_location_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_assets_last_verified_location_id_asset_locations",
        "assets",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_assets_current_location_id_asset_locations",
        "assets",
        type_="foreignkey",
    )
