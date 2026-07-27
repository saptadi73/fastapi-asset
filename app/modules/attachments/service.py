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
from app.modules.attachments.schemas import AttachmentCreate, AttachmentUpdate
from app.modules.maintenance.repository import (
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
            async with self.session.begin():
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
        except IntegrityError as exc:
            raise AppError(
                code="ATTACHMENT_CONFLICT",
                message="Attachment atau file metadata menimbulkan konflik.",
                status_code=409,
            ) from exc

        result = await self.get_attachment(attachment.id)
        return result

    async def get_attachment(self, attachment_id: UUID) -> Attachment:
        attachment = await self.attachments.get(attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError(str(attachment_id))
        return attachment

    async def update_attachment(
        self,
        attachment_id: UUID,
        payload: AttachmentUpdate,
    ) -> Attachment:
        attachment = await self.get_attachment(attachment_id)
        changes = payload.model_dump(exclude_unset=True, mode="python")

        async with self.session.begin():
            if (
                changes.get("is_primary") is True
                and attachment.entity_type == AttachmentEntityType.ASSET.value
                and attachment.attachment_category == AttachmentCategory.ASSET_PROFILE_PHOTO.value
            ):
                await self.attachments.unset_primary_asset_photo(asset_id=attachment.entity_id)

            for key, value in changes.items():
                setattr(attachment, key, value)
            await self.session.flush()

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

        raise AppError(
            code="ATTACHMENT_ENTITY_TYPE_UNSUPPORTED",
            message="Entity type attachment belum didukung.",
            status_code=422,
            details={"entity_type": entity_type},
        )
