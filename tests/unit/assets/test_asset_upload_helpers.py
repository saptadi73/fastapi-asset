from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import UploadFile
from unittest.mock import AsyncMock

from app.modules.assets.routes import _upload_asset_registry_files
from app.modules.attachments.constants import AttachmentCategory


@pytest.mark.asyncio
async def test_upload_asset_registry_files_maps_categories_and_primary_photo():
    actor_id = uuid4()
    asset_id = uuid4()
    attachment_service = SimpleNamespace(
        list_entity_attachments=AsyncMock(return_value=[]),
        create_uploaded_asset_attachment=AsyncMock(
            side_effect=[
                SimpleNamespace(id=uuid4(), sequence_no=1),
                SimpleNamespace(id=uuid4(), sequence_no=2),
                SimpleNamespace(id=uuid4(), sequence_no=3),
            ]
        ),
    )

    attachments = await _upload_asset_registry_files(
        attachment_service=attachment_service,
        asset_id=asset_id,
        photo_files=[UploadFile(filename="asset-photo.jpg", file=BytesIO(b"photo"))],
        manual_book_files=[UploadFile(filename="manual.pdf", file=BytesIO(b"manual"))],
        supporting_document_files=[
            UploadFile(filename="lampiran.txt", file=BytesIO(b"supporting"))
        ],
        actor_id=actor_id,
    )

    assert len(attachments) == 3
    calls = attachment_service.create_uploaded_asset_attachment.await_args_list
    assert calls[0].kwargs["attachment_category"] == AttachmentCategory.ASSET_PROFILE_PHOTO
    assert calls[0].kwargs["is_primary"] is True
    assert calls[0].kwargs["sequence_no"] == 1
    assert calls[1].kwargs["attachment_category"] == AttachmentCategory.MANUAL_BOOK
    assert calls[1].kwargs["sequence_no"] == 2
    assert calls[2].kwargs["attachment_category"] == AttachmentCategory.OTHER
    assert calls[2].kwargs["sequence_no"] == 3


@pytest.mark.asyncio
async def test_upload_asset_registry_files_respects_existing_primary_photo_and_sequence():
    actor_id = uuid4()
    asset_id = uuid4()
    existing_photo = SimpleNamespace(
        sequence_no=4,
        attachment_category=AttachmentCategory.ASSET_PROFILE_PHOTO.value,
        is_primary=True,
    )
    existing_manual = SimpleNamespace(
        sequence_no=7,
        attachment_category=AttachmentCategory.MANUAL_BOOK.value,
        is_primary=False,
    )
    attachment_service = SimpleNamespace(
        list_entity_attachments=AsyncMock(return_value=[existing_photo, existing_manual]),
        create_uploaded_asset_attachment=AsyncMock(
            return_value=SimpleNamespace(id=uuid4(), sequence_no=8)
        ),
    )

    await _upload_asset_registry_files(
        attachment_service=attachment_service,
        asset_id=asset_id,
        photo_files=[UploadFile(filename="new-photo.jpg", file=BytesIO(b"photo"))],
        manual_book_files=[],
        supporting_document_files=[],
        actor_id=actor_id,
    )

    call = attachment_service.create_uploaded_asset_attachment.await_args_list[0]
    assert call.kwargs["is_primary"] is False
    assert call.kwargs["sequence_no"] == 8
