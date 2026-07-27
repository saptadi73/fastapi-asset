from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.attachments.constants import (
    AttachmentCategory,
    AttachmentEntityType,
    AttachmentSource,
    AttachmentVisibility,
    FileKind,
    ScanStatus,
)


class FileCreate(BaseModel):
    tenant_id: UUID | None = None
    original_filename: str = Field(max_length=255)
    display_name: str = Field(max_length=255)
    file_kind: FileKind
    mime_type: str = Field(max_length=150)
    extension: str | None = Field(default=None, max_length=20)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    storage_provider: str = Field(max_length=30)
    storage_bucket: str = Field(max_length=100)
    storage_object_key: str = Field(max_length=500)
    scan_status: ScanStatus = ScanStatus.CLEAN
    scan_result: str | None = None
    is_encrypted: bool = True
    is_active: bool = True
    uploaded_by: UUID | None = None
    uploaded_at: datetime
    retention_until: date | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    original_filename: str
    display_name: str
    file_kind: str
    mime_type: str
    extension: str | None
    size_bytes: int
    checksum_sha256: str
    storage_provider: str
    storage_bucket: str
    storage_object_key: str
    current_version_no: int
    scan_status: str
    scan_result: str | None
    is_encrypted: bool
    is_active: bool
    uploaded_by: UUID | None
    uploaded_at: datetime
    retention_until: date | None
    metadata_json: dict | None = Field(
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )


class FileVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    version_no: int
    storage_bucket: str
    storage_object_key: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    change_notes: str | None
    uploaded_by: UUID | None
    uploaded_at: datetime
    is_current: bool


class FileVersionCreate(BaseModel):
    original_filename: str = Field(max_length=255)
    display_name: str = Field(max_length=255)
    mime_type: str = Field(max_length=150)
    extension: str | None = Field(default=None, max_length=20)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    storage_bucket: str = Field(max_length=100)
    storage_object_key: str = Field(max_length=500)
    uploaded_at: datetime
    change_notes: str | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")


class AttachmentCreate(BaseModel):
    file: FileCreate
    tenant_id: UUID | None = None
    entity_type: AttachmentEntityType
    entity_id: UUID
    attachment_category: AttachmentCategory
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    captured_at: datetime | None = None
    captured_by: UUID | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    sequence_no: int = Field(default=1, ge=1)
    is_primary: bool = False
    visibility: AttachmentVisibility = AttachmentVisibility.INTERNAL
    source: AttachmentSource = AttachmentSource.UPLOAD
    created_by: UUID | None = None
    created_at: datetime


class AttachmentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    sequence_no: int | None = Field(default=None, ge=1)
    is_primary: bool | None = None
    visibility: AttachmentVisibility | None = None
    deleted_by: UUID | None = None
    deleted_at: datetime | None = None


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    file_id: UUID
    entity_type: str
    entity_id: UUID
    attachment_category: str
    title: str | None
    description: str | None
    captured_at: datetime | None
    captured_by: UUID | None
    latitude: Decimal | None
    longitude: Decimal | None
    sequence_no: int
    is_primary: bool
    visibility: str
    source: str
    created_by: UUID | None
    created_at: datetime
    deleted_by: UUID | None
    deleted_at: datetime | None
    file: FileRead


class AttachmentDownloadRead(BaseModel):
    attachment: AttachmentRead
    current_version: FileVersionRead | None = None
    download_url: str | None = None
    download_mode: str = "STORAGE_REFERENCE"


class AttachmentAuditEventRead(BaseModel):
    event_type: str
    occurred_at: datetime
    actor_id: UUID | None = None
    version_no: int | None = None
    summary: str
    details: dict | None = None
