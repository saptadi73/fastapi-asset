from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.assets.repository import AssetRepository, AssetTransferRepository
from app.modules.attachments.constants import AttachmentCategory, AttachmentEntityType
from app.modules.attachments.exceptions import AttachmentNotFoundError
from app.modules.attachments.models import Attachment, File, FileVersion
from app.modules.attachments.repository import (
    AttachmentRepository,
    FileRepository,
    FileVersionRepository,
)
from app.modules.attachments.schemas import (
    AttachmentAuditEventRead,
    AttachmentCreate,
    AttachmentDownloadRead,
    AttachmentRead,
    AttachmentUpdate,
    FileVersionCreate,
    FileVersionRead,
)
from app.modules.maintenance.repository import (
    AssetFailureRepository,
    MaintenanceFindingRepository,
    MaintenanceRequestRepository,
    MaintenanceWorkOrderRepository,
)


class AttachmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.files = FileRepository(session)
        self.file_versions = FileVersionRepository(session)
        self.attachments = AttachmentRepository(session)
        self.assets = AssetRepository(session)
        self.transfers = AssetTransferRepository(session)
        self.asset_failures = AssetFailureRepository(session)
        self.maintenance_findings = MaintenanceFindingRepository(session)
        self.maintenance_requests = MaintenanceRequestRepository(session)
        self.maintenance_work_orders = MaintenanceWorkOrderRepository(session)

    async def create_attachment(self, payload: AttachmentCreate) -> Attachment:
        await self._validate_entity(payload.entity_type.value, payload.entity_id)

        file_record = File(
            tenant_id=payload.file.tenant_id,
            original_filename=payload.file.original_filename,
            display_name=payload.file.display_name,
            file_kind=payload.file.file_kind.value,
            mime_type=payload.file.mime_type,
            extension=payload.file.extension,
            size_bytes=payload.file.size_bytes,
            checksum_sha256=payload.file.checksum_sha256,
            storage_provider=payload.file.storage_provider,
            storage_bucket=payload.file.storage_bucket,
            storage_object_key=payload.file.storage_object_key,
            current_version_no=1,
            scan_status=payload.file.scan_status.value,
            scan_result=payload.file.scan_result,
            is_encrypted=payload.file.is_encrypted,
            is_active=payload.file.is_active,
            uploaded_by=payload.file.uploaded_by,
            uploaded_at=payload.file.uploaded_at,
            retention_until=payload.file.retention_until,
            metadata_json=payload.file.metadata_json,
            version=1,
        )

        attachment = Attachment(
            tenant_id=payload.tenant_id,
            entity_type=payload.entity_type.value,
            entity_id=payload.entity_id,
            attachment_category=payload.attachment_category.value,
            title=payload.title,
            description=payload.description,
            captured_at=payload.captured_at,
            captured_by=payload.captured_by,
            latitude=payload.latitude,
            longitude=payload.longitude,
            sequence_no=payload.sequence_no,
            is_primary=payload.is_primary,
            visibility=payload.visibility.value,
            source=payload.source.value,
            created_by=payload.created_by,
            created_at=payload.created_at,
        )

        try:
            created_file = await self.files.create(file_record)
            await self.file_versions.create(
                FileVersion(
                    file_id=created_file.id,
                    version_no=1,
                    storage_bucket=created_file.storage_bucket,
                    storage_object_key=created_file.storage_object_key,
                    mime_type=created_file.mime_type,
                    size_bytes=created_file.size_bytes,
                    checksum_sha256=created_file.checksum_sha256,
                    uploaded_by=created_file.uploaded_by,
                    uploaded_at=created_file.uploaded_at,
                    is_current=True,
                )
            )

            if (
                payload.entity_type == AttachmentEntityType.ASSET
                and payload.attachment_category == AttachmentCategory.ASSET_PROFILE_PHOTO
                and payload.is_primary
            ):
                await self.attachments.unset_primary_asset_photo(asset_id=payload.entity_id)

            attachment.file_id = created_file.id
            await self.attachments.create(attachment)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ATTACHMENT_CONFLICT",
                message="Attachment atau file metadata menimbulkan konflik.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        result = await self.get_attachment(attachment.id)
        return result

    async def get_attachment(self, attachment_id: UUID) -> Attachment:
        attachment = await self.attachments.get(attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError(str(attachment_id))
        return attachment

    async def get_attachment_download(self, attachment_id: UUID) -> AttachmentDownloadRead:
        attachment = await self.get_attachment(attachment_id)
        file_record = await self.files.get(attachment.file_id)
        if file_record is None:
            raise AppError(
                code="ATTACHMENT_FILE_NOT_FOUND",
                message="File attachment tidak ditemukan.",
                status_code=404,
            )

        current_version = next(
            (version for version in file_record.versions if version.is_current),
            None,
        )
        return AttachmentDownloadRead(
            attachment=AttachmentRead.model_validate(attachment),
            current_version=(
                FileVersionRead.model_validate(current_version)
                if current_version is not None
                else None
            ),
            download_url=None,
        )

    async def list_attachment_versions(self, attachment_id: UUID) -> list[FileVersion]:
        attachment = await self.get_attachment(attachment_id)
        items = await self.file_versions.list_by_file(attachment.file_id)
        return list(items)

    async def upload_attachment_version(
        self,
        attachment_id: UUID,
        payload: FileVersionCreate,
        *,
        uploaded_by: UUID | None,
    ) -> Attachment:
        attachment = await self.get_attachment(attachment_id)
        file_record = await self.files.get(attachment.file_id)
        if file_record is None:
            raise AppError(
                code="ATTACHMENT_FILE_NOT_FOUND",
                message="File attachment tidak ditemukan.",
                status_code=404,
            )

        current_versions = [version for version in file_record.versions if version.is_current]
        next_version_no = file_record.current_version_no + 1

        try:
            for version in current_versions:
                version.is_current = False

            file_record.original_filename = payload.original_filename
            file_record.display_name = payload.display_name
            file_record.mime_type = payload.mime_type
            file_record.extension = payload.extension
            file_record.size_bytes = payload.size_bytes
            file_record.checksum_sha256 = payload.checksum_sha256
            file_record.storage_bucket = payload.storage_bucket
            file_record.storage_object_key = payload.storage_object_key
            file_record.current_version_no = next_version_no
            file_record.uploaded_by = uploaded_by
            file_record.uploaded_at = payload.uploaded_at
            if payload.metadata_json is not None:
                file_record.metadata_json = payload.metadata_json

            await self.file_versions.create(
                FileVersion(
                    file_id=file_record.id,
                    version_no=next_version_no,
                    storage_bucket=payload.storage_bucket,
                    storage_object_key=payload.storage_object_key,
                    mime_type=payload.mime_type,
                    size_bytes=payload.size_bytes,
                    checksum_sha256=payload.checksum_sha256,
                    change_notes=payload.change_notes,
                    uploaded_by=uploaded_by,
                    uploaded_at=payload.uploaded_at,
                    is_current=True,
                )
            )
            await self.session.flush()
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ATTACHMENT_VERSION_CONFLICT",
                message="Versi file attachment menimbulkan konflik penyimpanan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        return await self.get_attachment(attachment_id)

    async def get_attachment_audit_trail(
        self,
        attachment_id: UUID,
    ) -> list[AttachmentAuditEventRead]:
        attachment = await self.get_attachment(attachment_id)
        file_record = await self.files.get(attachment.file_id)
        if file_record is None:
            raise AppError(
                code="ATTACHMENT_FILE_NOT_FOUND",
                message="File attachment tidak ditemukan.",
                status_code=404,
            )

        versions = list(await self.file_versions.list_by_file(file_record.id))
        events: list[AttachmentAuditEventRead] = [
            AttachmentAuditEventRead(
                event_type="ATTACHMENT_CREATED",
                occurred_at=attachment.created_at,
                actor_id=attachment.created_by,
                version_no=1,
                summary="Attachment dibuat.",
                details={
                    "entity_type": attachment.entity_type,
                    "entity_id": str(attachment.entity_id),
                    "attachment_category": attachment.attachment_category,
                },
            )
        ]
        for version in sorted(versions, key=lambda item: (item.version_no, item.uploaded_at)):
            events.append(
                AttachmentAuditEventRead(
                    event_type="FILE_VERSION_UPLOADED",
                    occurred_at=version.uploaded_at,
                    actor_id=version.uploaded_by,
                    version_no=version.version_no,
                    summary=(
                        "Versi file awal diunggah."
                        if version.version_no == 1
                        else "Versi file baru diunggah."
                    ),
                    details={
                        "storage_bucket": version.storage_bucket,
                        "storage_object_key": version.storage_object_key,
                        "mime_type": version.mime_type,
                        "size_bytes": version.size_bytes,
                        "change_notes": version.change_notes,
                        "is_current": version.is_current,
                    },
                )
            )
        if attachment.deleted_at is not None:
            events.append(
                AttachmentAuditEventRead(
                    event_type="ATTACHMENT_DELETED",
                    occurred_at=attachment.deleted_at,
                    actor_id=attachment.deleted_by,
                    version_no=file_record.current_version_no,
                    summary="Attachment dihapus secara soft delete.",
                    details={"is_primary": attachment.is_primary},
                )
            )

        events.sort(key=lambda item: item.occurred_at)
        return events

    async def update_attachment(
        self,
        attachment_id: UUID,
        payload: AttachmentUpdate,
    ) -> Attachment:
        attachment = await self.get_attachment(attachment_id)
        changes = payload.model_dump(exclude_unset=True, mode="python")

        try:
            if (
                changes.get("is_primary") is True
                and attachment.entity_type == AttachmentEntityType.ASSET.value
                and attachment.attachment_category == AttachmentCategory.ASSET_PROFILE_PHOTO.value
            ):
                await self.attachments.unset_primary_asset_photo(asset_id=attachment.entity_id)

            for key, value in changes.items():
                setattr(attachment, key, value)
            await self.session.flush()
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return await self.get_attachment(attachment_id)

    async def delete_attachment(
        self,
        attachment_id: UUID,
        *,
        deleted_by: UUID | None,
        deleted_at,
    ) -> Attachment:
        return await self.update_attachment(
            attachment_id,
            AttachmentUpdate(
                deleted_by=deleted_by,
                deleted_at=deleted_at,
                is_primary=False,
            ),
        )

    async def list_entity_attachments(
        self,
        *,
        entity_type: str,
        entity_id: UUID,
    ) -> list[Attachment]:
        await self._validate_entity(entity_type, entity_id)
        items = await self.attachments.list_by_entity(entity_type=entity_type, entity_id=entity_id)
        return list(items)

    async def _validate_entity(self, entity_type: str, entity_id: UUID) -> None:
        if entity_type == AttachmentEntityType.ASSET.value:
            asset = await self.assets.get(entity_id)
            if asset is None:
                raise AppError(
                    code="ATTACHMENT_ENTITY_NOT_FOUND",
                    message="Entity target attachment tidak ditemukan.",
                    status_code=404,
                    details={"entity_type": entity_type, "entity_id": str(entity_id)},
                )
            return

        if entity_type == AttachmentEntityType.ASSET_TRANSFER.value:
            transfer = await self.transfers.get(entity_id)
            if transfer is None:
                raise AppError(
                    code="ATTACHMENT_ENTITY_NOT_FOUND",
                    message="Entity target attachment tidak ditemukan.",
                    status_code=404,
                    details={"entity_type": entity_type, "entity_id": str(entity_id)},
                )
            return

        if entity_type == AttachmentEntityType.MAINTENANCE_REQUEST.value:
            maintenance_request = await self.maintenance_requests.get(entity_id)
            if maintenance_request is None:
                raise AppError(
                    code="ATTACHMENT_ENTITY_NOT_FOUND",
                    message="Entity target attachment tidak ditemukan.",
                    status_code=404,
                    details={"entity_type": entity_type, "entity_id": str(entity_id)},
                )
            return

        if entity_type == AttachmentEntityType.MAINTENANCE_WORK_ORDER.value:
            work_order = await self.maintenance_work_orders.get(entity_id)
            if work_order is None:
                raise AppError(
                    code="ATTACHMENT_ENTITY_NOT_FOUND",
                    message="Entity target attachment tidak ditemukan.",
                    status_code=404,
                    details={"entity_type": entity_type, "entity_id": str(entity_id)},
                )
            return

        if entity_type == AttachmentEntityType.MAINTENANCE_FINDING.value:
            finding = await self.maintenance_findings.get(entity_id)
            if finding is None:
                raise AppError(
                    code="ATTACHMENT_ENTITY_NOT_FOUND",
                    message="Entity target attachment tidak ditemukan.",
                    status_code=404,
                    details={"entity_type": entity_type, "entity_id": str(entity_id)},
                )
            return

        if entity_type == AttachmentEntityType.ASSET_FAILURE.value:
            failure = await self.asset_failures.get(entity_id)
            if failure is None:
                raise AppError(
                    code="ATTACHMENT_ENTITY_NOT_FOUND",
                    message="Entity target attachment tidak ditemukan.",
                    status_code=404,
                    details={"entity_type": entity_type, "entity_id": str(entity_id)},
                )
            return

        raise AppError(
            code="ATTACHMENT_ENTITY_TYPE_UNSUPPORTED",
            message="Entity type attachment belum didukung.",
            status_code=422,
            details={"entity_type": entity_type},
        )
