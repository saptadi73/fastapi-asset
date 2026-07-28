from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.assets.models import Asset
from app.modules.tracking.models import (
    AssetScanEvent,
    AssetStocktakeExpectedItem,
    AssetStocktakeResult,
    AssetStocktakeSession,
    AssetVerification,
)
from app.shared.pagination import PaginationParams


class AssetTrackingAssetLookupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_tracking_code(self, raw_tag_uid: str) -> Asset | None:
        stmt = select(Asset).where(
            or_(
                Asset.asset_code == raw_tag_uid,
                Asset.tag_number == raw_tag_uid,
                Asset.barcode == raw_tag_uid,
                Asset.qr_code == raw_tag_uid,
                Asset.serial_number == raw_tag_uid,
            )
        )
        return await self.session.scalar(stmt)

    async def list_by_location(self, location_id: UUID) -> Sequence[Asset]:
        stmt = (
            select(Asset)
            .where(Asset.current_location_id == location_id)
            .order_by(Asset.asset_code)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetScanEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetScanEvent) -> AssetScanEvent:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["asset", "scanned_location", "stocktake_session"],
        )
        return item

    async def get(self, scan_event_id: UUID) -> AssetScanEvent | None:
        stmt = (
            select(AssetScanEvent)
            .options(
                selectinload(AssetScanEvent.asset),
                selectinload(AssetScanEvent.scanned_location),
                selectinload(AssetScanEvent.stocktake_session),
            )
            .where(AssetScanEvent.id == scan_event_id)
        )
        return await self.session.scalar(stmt)

    async def get_by_event_uid(self, event_uid: UUID) -> AssetScanEvent | None:
        stmt = (
            select(AssetScanEvent)
            .options(
                selectinload(AssetScanEvent.asset),
                selectinload(AssetScanEvent.scanned_location),
                selectinload(AssetScanEvent.stocktake_session),
            )
            .where(AssetScanEvent.event_uid == event_uid)
        )
        return await self.session.scalar(stmt)

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetScanEvent]:
        stmt = (
            select(AssetScanEvent)
            .options(selectinload(AssetScanEvent.scanned_location))
            .where(AssetScanEvent.asset_id == asset_id)
            .order_by(AssetScanEvent.scanned_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetVerificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetVerification) -> AssetVerification:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetVerification]:
        stmt = (
            select(AssetVerification)
            .options(
                selectinload(AssetVerification.expected_location),
                selectinload(AssetVerification.observed_location),
            )
            .where(AssetVerification.asset_id == asset_id)
            .order_by(AssetVerification.verified_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def list_location_discrepancies(
        self,
        pagination: PaginationParams,
        *,
        resolution_status: str | None = None,
        location_id: UUID | None = None,
    ) -> tuple[Sequence[AssetVerification], int]:
        stmt: Select[tuple[AssetVerification]] = (
            select(AssetVerification)
            .options(
                selectinload(AssetVerification.asset),
                selectinload(AssetVerification.expected_location),
                selectinload(AssetVerification.observed_location),
            )
            .where(
                AssetVerification.verification_result == "PRESENT_WRONG_LOCATION"
            )
        )
        count_stmt = (
            select(func.count())
            .select_from(AssetVerification)
            .where(AssetVerification.verification_result == "PRESENT_WRONG_LOCATION")
        )

        if pagination.search:
            search_value = f"%{pagination.search}%"
            stmt = stmt.join(Asset, Asset.id == AssetVerification.asset_id)
            count_stmt = count_stmt.join(Asset, Asset.id == AssetVerification.asset_id)
            search_filter = or_(
                Asset.asset_code.ilike(search_value),
                Asset.asset_name.ilike(search_value),
                Asset.tag_number.ilike(search_value),
                Asset.serial_number.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if resolution_status:
            stmt = stmt.where(AssetVerification.resolution_status == resolution_status)
            count_stmt = count_stmt.where(AssetVerification.resolution_status == resolution_status)

        if location_id:
            location_filter = or_(
                AssetVerification.expected_location_id == location_id,
                AssetVerification.observed_location_id == location_id,
            )
            stmt = stmt.where(location_filter)
            count_stmt = count_stmt.where(location_filter)

        sort_column = getattr(AssetVerification, pagination.sort or "verified_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items


class AssetStocktakeSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetStocktakeSession) -> AssetStocktakeSession:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["location"])
        return item

    async def get(self, stocktake_session_id: UUID) -> AssetStocktakeSession | None:
        stmt = (
            select(AssetStocktakeSession)
            .options(
                selectinload(AssetStocktakeSession.location),
                selectinload(AssetStocktakeSession.expected_items).selectinload(
                    AssetStocktakeExpectedItem.asset
                ),
                selectinload(AssetStocktakeSession.results).selectinload(
                    AssetStocktakeResult.asset
                ),
                selectinload(AssetStocktakeSession.results).selectinload(
                    AssetStocktakeResult.observed_location
                ),
            )
            .where(AssetStocktakeSession.id == stocktake_session_id)
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        pagination: PaginationParams,
        *,
        status_filter: str | None = None,
        location_id: UUID | None = None,
    ) -> tuple[Sequence[AssetStocktakeSession], int]:
        stmt: Select[tuple[AssetStocktakeSession]] = select(AssetStocktakeSession).options(
            selectinload(AssetStocktakeSession.location),
            selectinload(AssetStocktakeSession.expected_items),
            selectinload(AssetStocktakeSession.results),
        )
        count_stmt = select(func.count()).select_from(AssetStocktakeSession)

        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                AssetStocktakeSession.session_number.ilike(search_value),
                AssetStocktakeSession.notes.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if status_filter:
            stmt = stmt.where(AssetStocktakeSession.status == status_filter)
            count_stmt = count_stmt.where(AssetStocktakeSession.status == status_filter)

        if location_id:
            stmt = stmt.where(AssetStocktakeSession.location_id == location_id)
            count_stmt = count_stmt.where(AssetStocktakeSession.location_id == location_id)

        sort_column = getattr(AssetStocktakeSession, pagination.sort or "planned_start_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(
        self,
        item: AssetStocktakeSession,
        **changes: object,
    ) -> AssetStocktakeSession:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["location"])
        return item


class AssetStocktakeExpectedItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(
        self,
        items: list[AssetStocktakeExpectedItem],
    ) -> list[AssetStocktakeExpectedItem]:
        self.session.add_all(items)
        await self.session.flush()
        return items

    async def list_by_session(
        self,
        stocktake_session_id: UUID,
    ) -> Sequence[AssetStocktakeExpectedItem]:
        stmt = (
            select(AssetStocktakeExpectedItem)
            .options(selectinload(AssetStocktakeExpectedItem.asset))
            .where(AssetStocktakeExpectedItem.stocktake_session_id == stocktake_session_id)
            .order_by(AssetStocktakeExpectedItem.id)
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_by_session_and_asset(
        self,
        *,
        stocktake_session_id: UUID,
        asset_id: UUID,
    ) -> AssetStocktakeExpectedItem | None:
        stmt = select(AssetStocktakeExpectedItem).where(
            and_(
                AssetStocktakeExpectedItem.stocktake_session_id == stocktake_session_id,
                AssetStocktakeExpectedItem.asset_id == asset_id,
            )
        )
        return await self.session.scalar(stmt)


class AssetStocktakeResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetStocktakeResult) -> AssetStocktakeResult:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_session(self, stocktake_session_id: UUID) -> Sequence[AssetStocktakeResult]:
        stmt = (
            select(AssetStocktakeResult)
            .options(
                selectinload(AssetStocktakeResult.asset),
                selectinload(AssetStocktakeResult.observed_location),
                selectinload(AssetStocktakeResult.scan_event),
            )
            .where(AssetStocktakeResult.stocktake_session_id == stocktake_session_id)
            .order_by(AssetStocktakeResult.observed_at.desc().nullslast(), AssetStocktakeResult.id)
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def list_by_session_and_asset(
        self,
        *,
        stocktake_session_id: UUID,
        asset_id: UUID,
    ) -> Sequence[AssetStocktakeResult]:
        stmt = (
            select(AssetStocktakeResult)
            .where(
                and_(
                    AssetStocktakeResult.stocktake_session_id == stocktake_session_id,
                    AssetStocktakeResult.asset_id == asset_id,
                )
            )
            .order_by(AssetStocktakeResult.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def list_missing_assets(
        self,
        pagination: PaginationParams,
        *,
        stocktake_session_id: UUID | None = None,
        location_id: UUID | None = None,
        resolution_status: str | None = None,
    ) -> tuple[Sequence[AssetStocktakeResult], int]:
        stmt: Select[tuple[AssetStocktakeResult]] = (
            select(AssetStocktakeResult)
            .join(
                AssetStocktakeSession,
                AssetStocktakeSession.id == AssetStocktakeResult.stocktake_session_id,
            )
            .options(
                selectinload(AssetStocktakeResult.asset),
                selectinload(AssetStocktakeResult.observed_location),
                selectinload(AssetStocktakeResult.stocktake_session).selectinload(
                    AssetStocktakeSession.location
                ),
                selectinload(AssetStocktakeResult.stocktake_session).selectinload(
                    AssetStocktakeSession.expected_items
                ),
                selectinload(AssetStocktakeResult.stocktake_session).selectinload(
                    AssetStocktakeSession.results
                ),
            )
            .where(AssetStocktakeResult.result_type == "MISSING")
        )
        count_stmt = (
            select(func.count())
            .select_from(AssetStocktakeResult)
            .join(
                AssetStocktakeSession,
                AssetStocktakeSession.id == AssetStocktakeResult.stocktake_session_id,
            )
            .where(AssetStocktakeResult.result_type == "MISSING")
        )

        if pagination.search:
            search_value = f"%{pagination.search}%"
            stmt = stmt.join(Asset, Asset.id == AssetStocktakeResult.asset_id)
            count_stmt = count_stmt.join(Asset, Asset.id == AssetStocktakeResult.asset_id)
            search_filter = or_(
                Asset.asset_code.ilike(search_value),
                Asset.asset_name.ilike(search_value),
                Asset.tag_number.ilike(search_value),
                Asset.serial_number.ilike(search_value),
                AssetStocktakeSession.session_number.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if stocktake_session_id:
            stmt = stmt.where(AssetStocktakeResult.stocktake_session_id == stocktake_session_id)
            count_stmt = count_stmt.where(
                AssetStocktakeResult.stocktake_session_id == stocktake_session_id
            )

        if location_id:
            stmt = stmt.where(AssetStocktakeSession.location_id == location_id)
            count_stmt = count_stmt.where(AssetStocktakeSession.location_id == location_id)

        if resolution_status:
            stmt = stmt.where(AssetStocktakeResult.resolution_status == resolution_status)
            count_stmt = count_stmt.where(
                AssetStocktakeResult.resolution_status == resolution_status
            )

        sort_column = getattr(AssetStocktakeResult, pagination.sort or "created_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items


class AssetTrackingReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_unverified_assets(
        self,
        pagination: PaginationParams,
        *,
        verify_before: datetime,
        location_id: UUID | None = None,
    ) -> tuple[Sequence[Asset], int]:
        stmt: Select[tuple[Asset]] = select(Asset).options(
            selectinload(Asset.current_location),
            selectinload(Asset.asset_category),
            selectinload(Asset.asset_class),
        ).where(
            or_(
                Asset.last_verified_at.is_(None),
                Asset.last_verified_at < verify_before,
            )
        )
        count_stmt = select(func.count()).select_from(Asset).where(
            or_(
                Asset.last_verified_at.is_(None),
                Asset.last_verified_at < verify_before,
            )
        )

        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                Asset.asset_code.ilike(search_value),
                Asset.asset_name.ilike(search_value),
                Asset.tag_number.ilike(search_value),
                Asset.serial_number.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if location_id:
            stmt = stmt.where(Asset.current_location_id == location_id)
            count_stmt = count_stmt.where(Asset.current_location_id == location_id)

        sort_column = getattr(Asset, pagination.sort or "last_verified_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc().nullsfirst()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column, Asset.asset_code.asc()).offset(offset).limit(
            pagination.page_size
        )
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items
