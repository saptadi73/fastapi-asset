from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.attachments.constants import AttachmentCategory, AttachmentEntityType
from app.modules.attachments.models import Attachment, File, FileEvent, FileVersion


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, file_record: File) -> File:
        self.session.add(file_record)
        await self.session.flush()
        await self.session.refresh(file_record, attribute_names=["versions"])
        return file_record

    async def get(self, file_id: UUID) -> File | None:
        stmt = (
            select(File)
            .options(selectinload(File.versions))
            .where(File.id == file_id)
        )
        return await self.session.scalar(stmt)


class FileVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, version: FileVersion) -> FileVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def list_by_file(self, file_id: UUID) -> Sequence[FileVersion]:
        stmt = (
            select(FileVersion)
            .where(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_no.desc(), FileVersion.uploaded_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class FileEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: FileEvent) -> FileEvent:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_attachment(self, attachment_id: UUID) -> Sequence[FileEvent]:
        stmt = (
            select(FileEvent)
            .where(FileEvent.attachment_id == attachment_id)
            .order_by(FileEvent.occurred_at.asc(), FileEvent.id.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.flush()
        await self.session.refresh(attachment, attribute_names=["file"])
        return attachment

    async def get(self, attachment_id: UUID) -> Attachment | None:
        stmt = (
            select(Attachment)
            .options(selectinload(Attachment.file))
            .where(Attachment.id == attachment_id)
        )
        return await self.session.scalar(stmt)

    async def list_by_entity(
        self,
        *,
        entity_type: str,
        entity_id: UUID,
    ) -> Sequence[Attachment]:
        stmt = (
            select(Attachment)
            .options(selectinload(Attachment.file))
            .where(
                and_(
                    Attachment.entity_type == entity_type,
                    Attachment.entity_id == entity_id,
                    Attachment.deleted_at.is_(None),
                )
            )
            .order_by(Attachment.sequence_no.asc(), Attachment.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def unset_primary_asset_photo(
        self,
        *,
        asset_id: UUID,
    ) -> None:
        stmt = (
            select(Attachment)
            .where(
                and_(
                    Attachment.entity_type == AttachmentEntityType.ASSET.value,
                    Attachment.entity_id == asset_id,
                    Attachment.attachment_category == AttachmentCategory.ASSET_PROFILE_PHOTO.value,
                    Attachment.is_primary.is_(True),
                    Attachment.deleted_at.is_(None),
                )
            )
        )
        results = await self.session.scalars(stmt)
        for item in results:
            item.is_primary = False
        await self.session.flush()
