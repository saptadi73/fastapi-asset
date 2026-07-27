from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_session,
    require_attachment_read,
    require_attachment_write,
)
from app.core.exceptions import AppError
from app.modules.attachments.constants import AttachmentCategory, AttachmentEntityType
from app.modules.attachments.schemas import AttachmentCreate, AttachmentRead, AttachmentUpdate
from app.modules.attachments.service import AttachmentService
from app.modules.auth.models import AppUser
from app.shared.responses import success_response

router = APIRouter(prefix="/attachments")


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


@router.patch("/{attachment_id}", dependencies=[Depends(require_attachment_write)])
async def update_attachment(
    request: Request,
    attachment_id: UUID,
    payload: AttachmentUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    item = await service.update_attachment(attachment_id, payload)
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
