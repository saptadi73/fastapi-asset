from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BIGINT,
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.types import TimestampMixin, UUIDPrimaryKeyMixin


class File(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_files_size_bytes_positive"),
        CheckConstraint(
            "current_version_no > 0",
            name="ck_files_current_version_positive",
        ),
        UniqueConstraint(
            "storage_bucket",
            "storage_object_key",
            name="uq_files_storage_bucket_object_key",
        ),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(20))
    size_bytes: Mapped[int] = mapped_column(BIGINT, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    current_version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    scan_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    scan_result: Mapped[str | None] = mapped_column(Text)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uploaded_by: Mapped[UUID | None] = mapped_column(nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_by: Mapped[UUID | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_until: Mapped[date | None] = mapped_column(Date)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    versions: Mapped[list[FileVersion]] = relationship(back_populates="file")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="file")


class FileVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "file_versions"
    __table_args__ = (
        UniqueConstraint("file_id", "version_no", name="uq_file_versions_file_version"),
    )

    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BIGINT, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    change_notes: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[UUID | None] = mapped_column(nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    file: Mapped[File] = relationship(back_populates="versions")


class Attachment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attachments"

    tenant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    attachment_category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_by: Mapped[UUID | None] = mapped_column(nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    sequence_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="INTERNAL", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="UPLOAD", nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_by: Mapped[UUID | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    file: Mapped[File] = relationship(back_populates="attachments")
