from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.assets.repository import AssetRepository, AssetTransferRepository
from app.modules.attachments.constants import AttachmentCategory, AttachmentEntityType
from app.modules.attachments.exceptions import AttachmentNotFoundError
from app.modules.attachments.models import Attachment, File, FileEvent, FileVersion
from app.modules.attachments.repository import (
    AttachmentRepository,
    FileEventRepository,
    FileRepository,
    FileVersionRepository,
)
from app.modules.attachments.schemas import (
    AttachmentAuditEventRead,
    AttachmentCreate,
    AttachmentDownloadAccessRead,
    AttachmentDownloadRead,
    AttachmentRead,
    AttachmentUpdate,
    FileRead,
    FileVersionCreate,
    FileVersionRead,
)
from app.modules.maintenance.repository import (
    AssetFailureRepository,
    MaintenanceFindingRepository,
    MaintenanceRequestRepository,
    MaintenanceWorkOrderRepository,
)

settings = get_settings()


class AttachmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.files = FileRepository(session)
        self.file_versions = FileVersionRepository(session)
        self.file_events = FileEventRepository(session)
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
            created_version = await self.file_versions.create(
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
            created_attachment = await self.attachments.create(attachment)
            await self._append_file_event(
                file_id=created_file.id,
                attachment_id=created_attachment.id,
                file_version_id=created_version.id,
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
            await self._append_file_event(
                file_id=created_file.id,
                attachment_id=created_attachment.id,
                file_version_id=created_version.id,
                event_type="FILE_VERSION_UPLOADED",
                occurred_at=created_version.uploaded_at,
                actor_id=created_version.uploaded_by,
                version_no=1,
                summary="Versi file awal diunggah.",
                details={
                    "storage_bucket": created_version.storage_bucket,
                    "storage_object_key": created_version.storage_object_key,
                    "mime_type": created_version.mime_type,
                    "size_bytes": created_version.size_bytes,
                    "is_current": created_version.is_current,
                },
            )
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
        if current_version is None:
            raise AppError(
                code="ATTACHMENT_VERSION_NOT_FOUND",
                message="Versi aktif attachment tidak ditemukan.",
                status_code=404,
            )
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.attachment_download_token_minutes
        )
        token = self._encode_download_token(
            attachment_id=attachment.id,
            file_id=file_record.id,
            file_version_id=current_version.id,
            version_no=current_version.version_no,
            expires_at=expires_at,
        )
        await self._append_file_event(
            file_id=file_record.id,
            attachment_id=attachment.id,
            file_version_id=current_version.id,
            event_type="DOWNLOAD_LINK_ISSUED",
            occurred_at=datetime.now(UTC),
            actor_id=None,
            version_no=current_version.version_no,
            summary="Link download aman diterbitkan.",
            details={"expires_at": expires_at.isoformat()},
        )
        await self.session.commit()
        return AttachmentDownloadRead(
            attachment=AttachmentRead.model_validate(attachment),
            current_version=FileVersionRead.model_validate(current_version),
            download_url=f"{settings.api_v1_prefix}/attachments/downloads/{token}",
            expires_at=expires_at,
        )

    async def resolve_download_token(
        self,
        download_token: str,
    ) -> AttachmentDownloadAccessRead:
        claims = self._decode_download_token(download_token)
        attachment = await self.get_attachment(UUID(str(claims["attachment_id"])))
        file_record = await self.files.get(UUID(str(claims["file_id"])))
        if file_record is None:
            raise AppError(
                code="ATTACHMENT_FILE_NOT_FOUND",
                message="File attachment tidak ditemukan.",
                status_code=404,
            )

        version = next(
            (
                item
                for item in file_record.versions
                if item.id == UUID(str(claims["file_version_id"]))
            ),
            None,
        )
        if version is None:
            raise AppError(
                code="ATTACHMENT_VERSION_NOT_FOUND",
                message="Versi file attachment tidak ditemukan.",
                status_code=404,
            )

        expires_at = datetime.fromtimestamp(int(claims["exp"]), UTC)
        await self._append_file_event(
            file_id=file_record.id,
            attachment_id=attachment.id,
            file_version_id=version.id,
            event_type="DOWNLOAD_TOKEN_RESOLVED",
            occurred_at=datetime.now(UTC),
            actor_id=None,
            version_no=version.version_no,
            summary="Token download aman digunakan.",
            details={"expires_at": expires_at.isoformat()},
        )
        await self.session.commit()
        return AttachmentDownloadAccessRead(
            attachment=AttachmentRead.model_validate(attachment),
            file=FileRead.model_validate(file_record),
            version=FileVersionRead.model_validate(version),
            storage_provider=file_record.storage_provider,
            storage_bucket=version.storage_bucket,
            storage_object_key=version.storage_object_key,
            mime_type=version.mime_type,
            file_name=file_record.display_name,
            expires_at=expires_at,
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

            created_version = await self.file_versions.create(
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
            await self._append_file_event(
                file_id=file_record.id,
                attachment_id=attachment.id,
                file_version_id=created_version.id,
                event_type="FILE_VERSION_UPLOADED",
                occurred_at=payload.uploaded_at,
                actor_id=uploaded_by,
                version_no=next_version_no,
                summary="Versi file baru diunggah.",
                details={
                    "storage_bucket": payload.storage_bucket,
                    "storage_object_key": payload.storage_object_key,
                    "mime_type": payload.mime_type,
                    "size_bytes": payload.size_bytes,
                    "change_notes": payload.change_notes,
                    "is_current": True,
                },
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

        events = await self.file_events.list_by_attachment(attachment.id)
        return [
            AttachmentAuditEventRead(
                event_type=item.event_type,
                occurred_at=item.occurred_at,
                actor_id=item.actor_id,
                version_no=item.version_no,
                summary=item.summary,
                details=item.details_json,
            )
            for item in events
        ]

    async def update_attachment(
        self,
        attachment_id: UUID,
        payload: AttachmentUpdate,
        *,
        actor_id: UUID | None = None,
    ) -> Attachment:
        attachment = await self.get_attachment(attachment_id)
        changes = payload.model_dump(exclude_unset=True, mode="python")

        try:
            detail_changes: dict[str, object] = {}
            if (
                changes.get("is_primary") is True
                and attachment.entity_type == AttachmentEntityType.ASSET.value
                and attachment.attachment_category == AttachmentCategory.ASSET_PROFILE_PHOTO.value
            ):
                await self.attachments.unset_primary_asset_photo(asset_id=attachment.entity_id)

            for key, value in changes.items():
                detail_changes[key] = value.isoformat() if isinstance(value, datetime) else value
                setattr(attachment, key, value)
            await self._append_file_event(
                file_id=attachment.file_id,
                attachment_id=attachment.id,
                file_version_id=None,
                event_type="ATTACHMENT_UPDATED",
                occurred_at=datetime.now(UTC),
                actor_id=actor_id,
                version_no=attachment.file.current_version_no,
                summary="Metadata attachment diperbarui.",
                details=detail_changes,
            )
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
        attachment = await self.get_attachment(attachment_id)
        payload = AttachmentUpdate(
            deleted_by=deleted_by,
            deleted_at=deleted_at,
            is_primary=False,
        )
        await self.update_attachment(
            attachment_id,
            payload,
            actor_id=deleted_by,
        )
        await self._append_file_event(
            file_id=attachment.file_id,
            attachment_id=attachment.id,
            file_version_id=None,
            event_type="ATTACHMENT_DELETED",
            occurred_at=deleted_at,
            actor_id=deleted_by,
            version_no=attachment.file.current_version_no,
            summary="Attachment dihapus secara soft delete.",
            details={"is_primary": False},
        )
        await self.session.commit()
        return await self.get_attachment(attachment_id)

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

    async def _append_file_event(
        self,
        *,
        file_id: UUID,
        attachment_id: UUID | None,
        file_version_id: UUID | None,
        event_type: str,
        occurred_at: datetime,
        actor_id: UUID | None,
        version_no: int | None,
        summary: str,
        details: dict | None,
    ) -> FileEvent:
        return await self.file_events.create(
            FileEvent(
                file_id=file_id,
                attachment_id=attachment_id,
                file_version_id=file_version_id,
                event_type=event_type,
                occurred_at=occurred_at,
                actor_id=actor_id,
                version_no=version_no,
                summary=summary,
                details_json=details,
            )
        )

    def _encode_download_token(
        self,
        *,
        attachment_id: UUID,
        file_id: UUID,
        file_version_id: UUID,
        version_no: int,
        expires_at: datetime,
    ) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "type": "attachment_download",
                "attachment_id": str(attachment_id),
                "file_id": str(file_id),
                "file_version_id": str(file_version_id),
                "version_no": version_no,
                "iss": settings.jwt_issuer,
                "aud": settings.jwt_audience,
                "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def _decode_download_token(self, token: str) -> dict[str, object]:
        try:
            claims = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options={
                    "require": [
                        "type",
                        "attachment_id",
                        "file_id",
                        "file_version_id",
                        "version_no",
                        "iss",
                        "aud",
                        "iat",
                        "nbf",
                        "exp",
                    ]
                },
            )
        except jwt.InvalidTokenError as exc:
            raise AppError(
                code="ATTACHMENT_DOWNLOAD_TOKEN_INVALID",
                message="Token download attachment tidak valid atau sudah kedaluwarsa.",
                status_code=401,
            ) from exc
        if claims.get("type") != "attachment_download":
            raise AppError(
                code="ATTACHMENT_DOWNLOAD_TOKEN_INVALID",
                message="Jenis token download attachment tidak sesuai.",
                status_code=401,
            )
        return claims
