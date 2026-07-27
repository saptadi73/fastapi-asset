"""attachments initial

Revision ID: 20260727_2305
Revises: 20260727_2245
Create Date: 2026-07-27 23:05:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260727_2305"
down_revision = "20260727_2245"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("file_kind", sa.String(length=20), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("extension", sa.String(length=20), nullable=True),
        sa.Column("size_bytes", sa.BIGINT(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_provider", sa.String(length=30), nullable=False),
        sa.Column("storage_bucket", sa.String(length=100), nullable=False),
        sa.Column("storage_object_key", sa.String(length=500), nullable=False),
        sa.Column("current_version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("scan_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("scan_result", sa.Text(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retention_until", sa.Date(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_files_size_bytes_positive"),
        sa.CheckConstraint("current_version_no > 0", name="ck_files_current_version_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "storage_bucket",
            "storage_object_key",
            name="uq_files_storage_bucket_object_key",
        ),
    )

    op.create_table(
        "file_versions",
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("storage_bucket", sa.String(length=100), nullable=False),
        sa.Column("storage_object_key", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("size_bytes", sa.BIGINT(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("change_notes", sa.Text(), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_id", "version_no", name="uq_file_versions_file_version"),
    )

    op.create_table(
        "attachments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attachment_category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("captured_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("sequence_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="INTERNAL"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="UPLOAD"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_attachments_entity", "attachments", ["entity_type", "entity_id"])
    op.create_index("ix_files_checksum", "files", ["tenant_id", "checksum_sha256"])


def downgrade() -> None:
    op.drop_index("ix_files_checksum", table_name="files")
    op.drop_index("ix_attachments_entity", table_name="attachments")
    op.drop_table("attachments")
    op.drop_table("file_versions")
    op.drop_table("files")
