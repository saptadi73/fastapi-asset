from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.assets.exceptions import AssetLocationNotFoundError, AssetNotFoundError
from app.modules.assets.models import Asset
from app.modules.assets.repository import AssetLocationRepository, AssetRepository
from app.modules.tracking.constants import (
    MatchStatus,
    ProcessingStatus,
    ResolutionStatus,
    StocktakeResultType,
    StocktakeSnapshotStatus,
    StocktakeStatus,
    VerificationResult,
)
from app.modules.tracking.exceptions import StocktakeSessionNotFoundError
from app.modules.tracking.models import (
    AssetScanEvent,
    AssetStocktakeExpectedItem,
    AssetStocktakeResult,
    AssetStocktakeSession,
    AssetVerification,
)
from app.modules.tracking.repository import (
    AssetScanEventRepository,
    AssetStocktakeExpectedItemRepository,
    AssetStocktakeResultRepository,
    AssetStocktakeSessionRepository,
    AssetTrackingAssetLookupRepository,
    AssetTrackingReportRepository,
    AssetVerificationRepository,
)
from app.modules.tracking.schemas import (
    AssetScanEventCreate,
    AssetTrackingTimelineRead,
    LocationDiscrepancyReportItemRead,
    MissingAssetReportItemRead,
    StocktakeActionPayload,
    StocktakeSessionCreate,
    StocktakeSessionListItemRead,
    UnverifiedAssetReportItemRead,
)
from app.shared.pagination import PaginationParams


class AssetTrackingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.assets = AssetRepository(session)
        self.locations = AssetLocationRepository(session)
        self.asset_lookup = AssetTrackingAssetLookupRepository(session)
        self.scan_events = AssetScanEventRepository(session)
        self.verifications = AssetVerificationRepository(session)
        self.stocktakes = AssetStocktakeSessionRepository(session)
        self.stocktake_expected_items = AssetStocktakeExpectedItemRepository(session)
        self.stocktake_results = AssetStocktakeResultRepository(session)
        self.reports = AssetTrackingReportRepository(session)

    async def create_scan_event(self, payload: AssetScanEventCreate) -> AssetScanEvent:
        existing = await self.scan_events.get_by_event_uid(payload.event_uid)
        if existing is not None:
            return existing

        session = None
        if payload.stocktake_session_id is not None:
            session = await self.get_stocktake_session(payload.stocktake_session_id)
            if session.status != StocktakeStatus.IN_PROGRESS.value:
                raise AppError(
                    code="STOCKTAKE_SESSION_INVALID_STATUS",
                    message="Hanya stocktake IN_PROGRESS yang dapat menerima scan.",
                    status_code=409,
                )

        if payload.scanned_location_id is not None:
            location = await self.locations.get(payload.scanned_location_id)
            if location is None:
                raise AssetLocationNotFoundError(str(payload.scanned_location_id))

        asset = await self.asset_lookup.find_by_tracking_code(payload.raw_tag_uid)
        match_status = self._resolve_match_status(asset, payload.scanned_location_id)

        scan_event = AssetScanEvent(
            event_uid=payload.event_uid,
            asset_id=asset.id if asset else None,
            asset_tag_id=None,
            raw_tag_uid=payload.raw_tag_uid,
            scan_type=payload.scan_type.value,
            scan_source=payload.scan_source.value,
            device_id=payload.device_id,
            scanned_location_id=payload.scanned_location_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            gps_accuracy_meters=payload.gps_accuracy_meters,
            scanned_at=payload.scanned_at,
            received_at=payload.received_at,
            scanned_by=payload.scanned_by,
            transfer_id=payload.transfer_id,
            stocktake_session_id=payload.stocktake_session_id,
            match_status=match_status.value,
            processing_status=ProcessingStatus.PROCESSED.value,
            metadata_json=payload.metadata_json,
        )

        try:
            async with self.session.begin():
                created = await self.scan_events.create(scan_event)
                if asset is not None:
                    await self.assets.update(
                        asset,
                        last_verified_at=payload.scanned_at,
                        last_verified_location_id=payload.scanned_location_id,
                    )
                    await self.verifications.create(
                        self._build_verification(asset, created, payload.scanned_location_id)
                    )
                if session is not None:
                    await self._upsert_stocktake_result(session, created, asset)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_SCAN_EVENT_CONFLICT",
                message="Scan event menimbulkan konflik data.",
                status_code=409,
            ) from exc

        return await self._get_scan_event_or_raise(scan_event.id)

    async def create_scan_event_batch(
        self,
        payloads: list[AssetScanEventCreate],
    ) -> list[AssetScanEvent]:
        items: list[AssetScanEvent] = []
        for payload in payloads:
            items.append(await self.create_scan_event(payload))
        return items

    async def get_asset_tracking(self, asset_id: UUID) -> AssetTrackingTimelineRead:
        asset = await self.assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))

        scans = await self.scan_events.list_by_asset(asset_id)
        verifications = await self.verifications.list_by_asset(asset_id)
        return AssetTrackingTimelineRead(scans=list(scans), verifications=list(verifications))

    async def create_stocktake_session(
        self,
        payload: StocktakeSessionCreate,
    ) -> AssetStocktakeSession:
        location = await self.locations.get(payload.location_id)
        if location is None:
            raise AssetLocationNotFoundError(str(payload.location_id))

        item = AssetStocktakeSession(
            session_number=payload.session_number,
            location_id=payload.location_id,
            scope_type=payload.scope_type.value,
            status=StocktakeStatus.DRAFT.value,
            planned_start_at=payload.planned_start_at,
            planned_end_at=payload.planned_end_at,
            created_by=payload.created_by,
            notes=payload.notes,
        )
        try:
            async with self.session.begin():
                await self.stocktakes.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="STOCKTAKE_SESSION_CONFLICT",
                message="Session number stocktake sudah digunakan.",
                status_code=409,
            ) from exc
        return await self.get_stocktake_session(item.id)

    async def list_stocktake_sessions(
        self,
        pagination: PaginationParams,
        *,
        status_filter: str | None = None,
        location_id: UUID | None = None,
    ) -> tuple[list[AssetStocktakeSession], int]:
        items, total_items = await self.stocktakes.list(
            pagination,
            status_filter=status_filter,
            location_id=location_id,
        )
        return list(items), total_items

    async def get_stocktake_session(self, stocktake_session_id: UUID) -> AssetStocktakeSession:
        item = await self.stocktakes.get(stocktake_session_id)
        if item is None:
            raise StocktakeSessionNotFoundError(str(stocktake_session_id))
        return item

    async def start_stocktake(
        self,
        stocktake_session_id: UUID,
        payload: StocktakeActionPayload,
    ) -> AssetStocktakeSession:
        session = await self.get_stocktake_session(stocktake_session_id)
        if session.status != StocktakeStatus.DRAFT.value:
            raise AppError(
                code="STOCKTAKE_SESSION_INVALID_STATUS",
                message="Hanya stocktake DRAFT yang dapat dimulai.",
                status_code=409,
            )

        assets_in_scope = await self.asset_lookup.list_by_location(session.location_id)
        expected_items = [
            AssetStocktakeExpectedItem(
                stocktake_session_id=session.id,
                asset_id=asset.id,
                expected_location_id=session.location_id,
                expected_custodian_id=asset.current_primary_custodian_id,
                snapshot_status=StocktakeSnapshotStatus.EXPECTED.value,
            )
            for asset in assets_in_scope
        ]

        async with self.session.begin():
            await self.stocktakes.update(
                session,
                status=StocktakeStatus.IN_PROGRESS.value,
                started_at=payload.acted_at,
                notes=payload.notes or session.notes,
            )
            if expected_items:
                await self.stocktake_expected_items.create_many(expected_items)

        return await self.get_stocktake_session(stocktake_session_id)

    async def scan_stocktake(
        self,
        stocktake_session_id: UUID,
        payload: AssetScanEventCreate,
    ) -> AssetScanEvent:
        enriched_payload = payload.model_copy(update={"stocktake_session_id": stocktake_session_id})
        return await self.create_scan_event(enriched_payload)

    async def complete_stocktake(
        self,
        stocktake_session_id: UUID,
        payload: StocktakeActionPayload,
    ) -> AssetStocktakeSession:
        session = await self.get_stocktake_session(stocktake_session_id)
        if session.status != StocktakeStatus.IN_PROGRESS.value:
            raise AppError(
                code="STOCKTAKE_SESSION_INVALID_STATUS",
                message="Hanya stocktake IN_PROGRESS yang dapat diselesaikan.",
                status_code=409,
            )

        expected_items = await self.stocktake_expected_items.list_by_session(stocktake_session_id)
        existing_results = await self.stocktake_results.list_by_session(stocktake_session_id)
        captured_asset_ids = {
            result.asset_id
            for result in existing_results
            if result.asset_id is not None
            and result.result_type
            in {
                StocktakeResultType.FOUND.value,
                StocktakeResultType.WRONG_LOCATION.value,
                StocktakeResultType.UNEXPECTED.value,
                StocktakeResultType.DUPLICATE_TAG.value,
            }
        }

        async with self.session.begin():
            for expected_item in expected_items:
                if expected_item.asset_id not in captured_asset_ids:
                    await self.stocktake_results.create(
                        AssetStocktakeResult(
                            stocktake_session_id=stocktake_session_id,
                            asset_id=expected_item.asset_id,
                            scan_event_id=None,
                            result_type=StocktakeResultType.MISSING.value,
                            observed_location_id=None,
                            observed_at=None,
                            resolution_status=ResolutionStatus.OPEN.value,
                            notes="Aset belum ditemukan hingga sesi stocktake selesai.",
                        )
                    )

            await self.stocktakes.update(
                session,
                status=StocktakeStatus.COMPLETED.value,
                completed_at=payload.acted_at,
                notes=payload.notes or session.notes,
            )

        return await self.get_stocktake_session(stocktake_session_id)

    async def approve_stocktake(
        self,
        stocktake_session_id: UUID,
        payload: StocktakeActionPayload,
    ) -> AssetStocktakeSession:
        session = await self.get_stocktake_session(stocktake_session_id)
        if session.status != StocktakeStatus.COMPLETED.value:
            raise AppError(
                code="STOCKTAKE_SESSION_INVALID_STATUS",
                message="Hanya stocktake COMPLETED yang dapat diapprove.",
                status_code=409,
            )

        async with self.session.begin():
            await self.stocktakes.update(
                session,
                status=StocktakeStatus.APPROVED.value,
                approved_by=payload.actor_id,
                approved_at=payload.acted_at,
                notes=payload.notes or session.notes,
            )

            results = await self.stocktake_results.list_by_session(stocktake_session_id)
            for result in results:
                result.resolution_status = ResolutionStatus.APPROVED.value
                if not result.notes:
                    result.notes = "Hasil stocktake telah disetujui."

        return await self.get_stocktake_session(stocktake_session_id)

    async def get_location_discrepancies_report(
        self,
        pagination: PaginationParams,
        *,
        resolution_status: str | None = None,
        location_id: UUID | None = None,
    ) -> tuple[list[LocationDiscrepancyReportItemRead], int]:
        items, total_items = await self.verifications.list_location_discrepancies(
            pagination,
            resolution_status=resolution_status,
            location_id=location_id,
        )
        return [
            LocationDiscrepancyReportItemRead.model_validate(item)
            for item in items
        ], total_items

    async def get_missing_assets_report(
        self,
        pagination: PaginationParams,
        *,
        stocktake_session_id: UUID | None = None,
        location_id: UUID | None = None,
        resolution_status: str | None = None,
    ) -> tuple[list[MissingAssetReportItemRead], int]:
        items, total_items = await self.stocktake_results.list_missing_assets(
            pagination,
            stocktake_session_id=stocktake_session_id,
            location_id=location_id,
            resolution_status=resolution_status,
        )
        return [
            MissingAssetReportItemRead(
                id=item.id,
                stocktake_session_id=item.stocktake_session_id,
                asset_id=item.asset_id,
                result_type=item.result_type,
                observed_location_id=item.observed_location_id,
                observed_at=item.observed_at,
                resolution_status=item.resolution_status,
                resolution_reference_type=item.resolution_reference_type,
                resolution_reference_id=item.resolution_reference_id,
                notes=item.notes,
                created_at=item.created_at,
                asset=(
                    item.asset and {
                        "id": item.asset.id,
                        "asset_code": item.asset.asset_code,
                        "asset_name": item.asset.asset_name,
                        "tag_number": item.asset.tag_number,
                        "serial_number": item.asset.serial_number,
                    }
                ),
                stocktake_session=(
                    StocktakeSessionListItemRead.from_model(item.stocktake_session)
                    if getattr(item, "stocktake_session", None)
                    else None
                ),
            )
            for item in items
        ], total_items

    async def get_unverified_assets_report(
        self,
        pagination: PaginationParams,
        *,
        days_since_verified: int,
        location_id: UUID | None = None,
    ) -> tuple[list[UnverifiedAssetReportItemRead], int]:
        verify_before = datetime.now(UTC) - timedelta(days=days_since_verified)
        items, total_items = await self.reports.list_unverified_assets(
            pagination,
            verify_before=verify_before,
            location_id=location_id,
        )
        serialized: list[UnverifiedAssetReportItemRead] = []
        for item in items:
            age_days = None
            if item.last_verified_at is not None:
                age_days = (datetime.now(UTC) - item.last_verified_at).days
            serialized.append(
                UnverifiedAssetReportItemRead.from_model(
                    item,
                    verification_age_days=age_days,
                )
            )
        return serialized, total_items

    def _resolve_match_status(
        self,
        asset: Asset | None,
        scanned_location_id: UUID | None,
    ) -> MatchStatus:
        if asset is None:
            return MatchStatus.UNKNOWN_TAG
        if scanned_location_id is None:
            return MatchStatus.MATCHED
        if asset.current_location_id == scanned_location_id:
            return MatchStatus.EXPECTED_LOCATION
        return MatchStatus.UNEXPECTED_LOCATION

    def _build_verification(
        self,
        asset: Asset,
        scan_event: AssetScanEvent,
        observed_location_id: UUID | None,
    ) -> AssetVerification:
        if observed_location_id is None or observed_location_id == asset.current_location_id:
            result = VerificationResult.PRESENT_MATCH.value
        else:
            result = VerificationResult.PRESENT_WRONG_LOCATION.value

        return AssetVerification(
            asset_id=asset.id,
            scan_event_id=scan_event.id,
            expected_location_id=asset.current_location_id,
            observed_location_id=observed_location_id,
            verification_result=result,
            verified_at=scan_event.scanned_at,
            verified_by=scan_event.scanned_by,
            expected_custodian_id=asset.current_primary_custodian_id,
            observed_custodian_id=asset.current_primary_custodian_id,
            resolution_status=ResolutionStatus.OPEN.value,
            notes=f"Verifikasi otomatis dari scan {scan_event.scan_type}.",
        )

    async def _upsert_stocktake_result(
        self,
        session: AssetStocktakeSession,
        scan_event: AssetScanEvent,
        asset: Asset | None,
    ) -> None:
        if asset is None:
            await self.stocktake_results.create(
                AssetStocktakeResult(
                    stocktake_session_id=session.id,
                    asset_id=None,
                    scan_event_id=scan_event.id,
                    result_type=StocktakeResultType.UNKNOWN_TAG.value,
                    observed_location_id=scan_event.scanned_location_id,
                    observed_at=scan_event.scanned_at,
                    resolution_status=ResolutionStatus.OPEN.value,
                    notes=f"Tag {scan_event.raw_tag_uid} belum terdaftar.",
                )
            )
            return

        existing_results = await self.stocktake_results.list_by_session_and_asset(
            stocktake_session_id=session.id,
            asset_id=asset.id,
        )
        if any(
            item.result_type
            in {
                StocktakeResultType.FOUND.value,
                StocktakeResultType.WRONG_LOCATION.value,
                StocktakeResultType.UNEXPECTED.value,
            }
            for item in existing_results
        ):
            await self.stocktake_results.create(
                AssetStocktakeResult(
                    stocktake_session_id=session.id,
                    asset_id=asset.id,
                    scan_event_id=scan_event.id,
                    result_type=StocktakeResultType.DUPLICATE_TAG.value,
                    observed_location_id=scan_event.scanned_location_id,
                    observed_at=scan_event.scanned_at,
                    resolution_status=ResolutionStatus.OPEN.value,
                    notes="Aset yang sama dipindai lebih dari satu kali pada sesi stocktake ini.",
                )
            )
            return

        expected_item = await self.stocktake_expected_items.get_by_session_and_asset(
            stocktake_session_id=session.id,
            asset_id=asset.id,
        )

        if expected_item is None:
            result_type = StocktakeResultType.UNEXPECTED.value
            notes = "Aset ditemukan tetapi tidak termasuk snapshot expected items."
        elif expected_item.expected_location_id != scan_event.scanned_location_id:
            result_type = StocktakeResultType.WRONG_LOCATION.value
            notes = "Aset ditemukan tetapi berada di lokasi berbeda dari snapshot."
        else:
            result_type = StocktakeResultType.FOUND.value
            notes = "Aset ditemukan sesuai snapshot stocktake."

        await self.stocktake_results.create(
            AssetStocktakeResult(
                stocktake_session_id=session.id,
                asset_id=asset.id,
                scan_event_id=scan_event.id,
                result_type=result_type,
                observed_location_id=scan_event.scanned_location_id,
                observed_at=scan_event.scanned_at,
                resolution_status=ResolutionStatus.OPEN.value,
                notes=notes,
            )
        )

    async def _get_scan_event_or_raise(self, scan_event_id: UUID) -> AssetScanEvent:
        item = await self.scan_events.get(scan_event_id)
        if item is None:
            raise AppError(
                code="ASSET_SCAN_EVENT_NOT_FOUND",
                message="Asset scan event tidak ditemukan setelah dibuat.",
                status_code=404,
            )
        return item
