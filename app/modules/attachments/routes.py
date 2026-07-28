from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.compat import UTC
from app.core.config import get_settings
from app.api.dependencies import (
    get_current_user,
    get_session,
    require_attachment_read,
    require_attachment_write,
)
from app.core.exceptions import AppError
from app.modules.attachments.constants import AttachmentCategory, AttachmentEntityType
from app.modules.attachments.schemas import (
    AttachmentAuditEventRead,
    AttachmentCreate,
    AttachmentDownloadAccessRead,
    AttachmentDownloadRead,
    AttachmentRead,
    AttachmentUpdate,
    FileVersionCreate,
    FileVersionRead,
)
from app.modules.attachments.service import AttachmentService
from app.modules.auth.models import AppUser
from app.shared.responses import success_response

router = APIRouter(prefix="/attachments")
settings = get_settings()


@router.get("/downloads/{download_token}", dependencies=[Depends(require_attachment_read)])
async def resolve_attachment_download(
    request: Request,
    download_token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    item = await service.resolve_download_token(download_token)
    return success_response(
        request=request,
        message="Akses download attachment berhasil diresolusikan.",
        data=AttachmentDownloadAccessRead.model_validate(item).model_dump(
            mode="json",
            by_alias=True,
        ),
    )


@router.get("/downloads/{download_token}/file", dependencies=[Depends(require_attachment_read)])
async def download_attachment_file(
    download_token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    service = AttachmentService(session)
    item = await service.resolve_download_token(download_token)
    if item.storage_provider != "local":
        raise AppError(
            code="ATTACHMENT_DOWNLOAD_PROVIDER_UNSUPPORTED",
            message="Storage provider untuk direct download belum didukung.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"storage_provider": item.storage_provider},
        )

    storage_root = Path(settings.attachment_storage_root).resolve()
    file_path = (storage_root / item.storage_object_key).resolve()
    if not str(file_path).startswith(str(storage_root)):
        raise AppError(
            code="ATTACHMENT_DOWNLOAD_PATH_INVALID",
            message="Path file attachment tidak valid.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not file_path.exists() or not file_path.is_file():
        raise AppError(
            code="ATTACHMENT_FILE_NOT_FOUND",
            message="File attachment tidak ditemukan di storage lokal.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"storage_object_key": item.storage_object_key},
        )

    return FileResponse(
        path=file_path,
        media_type=item.mime_type,
        filename=item.file_name,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_attachment_write)],
)
async def create_attachment(
    request: Request,
    payload: AttachmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AttachmentService(session)
    item = await service.create_attachment(
        payload.model_copy(
            update={
                "created_by": current_user.id,
                "captured_by": payload.captured_by or current_user.id,
                "file": payload.file.model_copy(update={"uploaded_by": current_user.id}),
            }
        )
    )
    return success_response(
        request=request,
        message="Attachment berhasil dibuat.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get("/{attachment_id}", dependencies=[Depends(require_attachment_read)])
async def get_attachment(
    request: Request,
    attachment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    item = await service.get_attachment(attachment_id)
    return success_response(
        request=request,
        message="Detail attachment berhasil diambil.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get("/{attachment_id}/download", dependencies=[Depends(require_attachment_read)])
async def get_attachment_download(
    request: Request,
    attachment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    item = await service.get_attachment_download(attachment_id)
    return success_response(
        request=request,
        message="Referensi download attachment berhasil diambil.",
        data=AttachmentDownloadRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get("/{attachment_id}/versions", dependencies=[Depends(require_attachment_read)])
async def list_attachment_versions(
    request: Request,
    attachment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_attachment_versions(attachment_id)
    return success_response(
        request=request,
        message="Daftar versi attachment berhasil diambil.",
        data=[FileVersionRead.model_validate(item).model_dump(mode="json") for item in items],
    )


@router.post(
    "/{attachment_id}/versions",
    dependencies=[Depends(require_attachment_write)],
)
async def upload_attachment_version(
    request: Request,
    attachment_id: UUID,
    payload: FileVersionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AttachmentService(session)
    item = await service.upload_attachment_version(
        attachment_id,
        payload,
        uploaded_by=current_user.id,
    )
    return success_response(
        request=request,
        message="Versi baru attachment berhasil diunggah.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get("/{attachment_id}/audit-trail", dependencies=[Depends(require_attachment_read)])
async def get_attachment_audit_trail(
    request: Request,
    attachment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.get_attachment_audit_trail(attachment_id)
    return success_response(
        request=request,
        message="Audit trail attachment berhasil diambil.",
        data=[
            AttachmentAuditEventRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.patch("/{attachment_id}", dependencies=[Depends(require_attachment_write)])
async def update_attachment(
    request: Request,
    attachment_id: UUID,
    payload: AttachmentUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AttachmentService(session)
    item = await service.update_attachment(
        attachment_id,
        payload,
        actor_id=current_user.id,
    )
    return success_response(
        request=request,
        message="Attachment berhasil diperbarui.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.delete("/{attachment_id}", dependencies=[Depends(require_attachment_write)])
async def delete_attachment(
    request: Request,
    attachment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AttachmentService(session)
    item = await service.delete_attachment(
        attachment_id,
        deleted_by=current_user.id,
        deleted_at=datetime.now(UTC),
    )
    return success_response(
        request=request,
        message="Attachment berhasil dihapus.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get("/assets/{asset_id}", dependencies=[Depends(require_attachment_read)])
async def list_asset_attachments(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_entity_attachments(
        entity_type=AttachmentEntityType.ASSET.value,
        entity_id=asset_id,
    )
    return success_response(
        request=request,
        message="Daftar attachment asset berhasil diambil.",
        data=[
            AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in items
        ],
    )


@router.post(
    "/assets/{asset_id}",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_attachment_write)],
)
async def create_asset_attachment(
    request: Request,
    asset_id: UUID,
    payload: AttachmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AttachmentService(session)
    enriched_payload = payload.model_copy(
        update={
            "entity_type": AttachmentEntityType.ASSET,
            "entity_id": asset_id,
            "created_by": current_user.id,
            "captured_by": payload.captured_by or current_user.id,
            "file": payload.file.model_copy(update={"uploaded_by": current_user.id}),
        }
    )
    item = await service.create_attachment(enriched_payload)
    return success_response(
        request=request,
        message="Attachment asset berhasil dibuat.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get("/assets/{asset_id}/photos", dependencies=[Depends(require_attachment_read)])
async def list_asset_photos(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_entity_attachments(
        entity_type=AttachmentEntityType.ASSET.value,
        entity_id=asset_id,
    )
    photo_categories = {
        AttachmentCategory.ASSET_PROFILE_PHOTO.value,
        AttachmentCategory.ASSET_CONDITION_PHOTO.value,
        AttachmentCategory.NAMEPLATE_PHOTO.value,
        AttachmentCategory.SERIAL_NUMBER_PHOTO.value,
        AttachmentCategory.QR_RFID_TAG_PHOTO.value,
    }
    filtered = [item for item in items if item.attachment_category in photo_categories]
    return success_response(
        request=request,
        message="Daftar foto asset berhasil diambil.",
        data=[
            AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in filtered
        ],
    )


@router.post(
    "/assets/{asset_id}/primary-photo/{attachment_id}",
    dependencies=[Depends(require_attachment_write)],
)
async def set_asset_primary_photo(
    request: Request,
    asset_id: UUID,
    attachment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    attachment = await service.get_attachment(attachment_id)
    if (
        attachment.entity_type != AttachmentEntityType.ASSET.value
        or attachment.entity_id != asset_id
    ):
        raise AppError(
            code="ATTACHMENT_CONFLICT",
            message="Attachment bukan milik asset yang diminta.",
            status_code=status.HTTP_409_CONFLICT,
            details={"asset_id": str(asset_id), "attachment_id": str(attachment_id)},
        )
    item = await service.update_attachment(
        attachment_id,
        AttachmentUpdate(is_primary=True),
    )
    return success_response(
        request=request,
        message="Primary photo asset berhasil diatur.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )

