from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.schemas import AssetLocationRead
from app.modules.tracking.constants import ScanSource, ScanType, StocktakeScopeType


class TrackingAssetReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_code: str
    asset_name: str
    tag_number: str | None
    serial_number: str | None


class AssetScanEventCreate(BaseModel):
    event_uid: UUID
    raw_tag_uid: str = Field(max_length=255)
    scan_type: ScanType
    scan_source: ScanSource = ScanSource.API
    device_id: UUID | None = None
    scanned_location_id: UUID | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    gps_accuracy_meters: Decimal | None = None
    scanned_at: datetime
    received_at: datetime
    scanned_by: UUID | None = None
    transfer_id: UUID | None = None
    stocktake_session_id: UUID | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")


class AssetScanEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_uid: UUID
    asset_id: UUID | None
    asset_tag_id: UUID | None
    raw_tag_uid: str
    scan_type: str
    scan_source: str
    device_id: UUID | None
    scanned_location_id: UUID | None
    latitude: Decimal | None
    longitude: Decimal | None
    gps_accuracy_meters: Decimal | None
    scanned_at: datetime
    received_at: datetime
    scanned_by: UUID | None
    transfer_id: UUID | None
    stocktake_session_id: UUID | None
    match_status: str
    processing_status: str
    metadata_json: dict | None = Field(
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    asset: TrackingAssetReferenceRead | None = None
    scanned_location: AssetLocationRead | None = None


class AssetVerificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    scan_event_id: UUID
    expected_location_id: UUID | None
    observed_location_id: UUID | None
    verification_result: str
    verified_at: datetime
    verified_by: UUID | None
    expected_custodian_id: UUID | None
    observed_custodian_id: UUID | None
    resolution_status: str
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution_action: str | None
    notes: str | None
    expected_location: AssetLocationRead | None = None
    observed_location: AssetLocationRead | None = None


class AssetTrackingTimelineRead(BaseModel):
    scans: list[AssetScanEventRead]
    verifications: list[AssetVerificationRead]


class StocktakeSessionCreate(BaseModel):
    session_number: str = Field(max_length=50)
    location_id: UUID
    scope_type: StocktakeScopeType = StocktakeScopeType.LOCATION
    planned_start_at: datetime
    planned_end_at: datetime | None = None
    created_by: UUID | None = None
    notes: str | None = None


class StocktakeActionPayload(BaseModel):
    actor_id: UUID | None = None
    acted_at: datetime
    notes: str | None = None


class AssetStocktakeExpectedItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stocktake_session_id: UUID
    asset_id: UUID
    expected_location_id: UUID
    expected_custodian_id: UUID | None
    snapshot_status: str
    asset: TrackingAssetReferenceRead | None = None
    expected_location: AssetLocationRead | None = None


class AssetStocktakeResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stocktake_session_id: UUID
    asset_id: UUID | None
    scan_event_id: UUID | None
    result_type: str
    observed_location_id: UUID | None
    observed_at: datetime | None
    resolution_status: str
    resolution_reference_type: str | None
    resolution_reference_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    asset: TrackingAssetReferenceRead | None = None
    observed_location: AssetLocationRead | None = None


class StocktakeSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_number: str
    location_id: UUID
    scope_type: str
    status: str
    planned_start_at: datetime
    planned_end_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_by: UUID | None
    approved_by: UUID | None
    approved_at: datetime | None
    notes: str | None
    location: AssetLocationRead
    expected_item_count: int
    result_count: int
    expected_items: list[AssetStocktakeExpectedItemRead] = []
    results: list[AssetStocktakeResultRead] = []

    @classmethod
    def from_model(cls, item: object) -> StocktakeSessionRead:
        expected_items = [
            AssetStocktakeExpectedItemRead.model_validate(expected_item)
            for expected_item in getattr(item, "expected_items", [])
        ]
        results = [
            AssetStocktakeResultRead.model_validate(result)
            for result in getattr(item, "results", [])
        ]
        return cls(
            id=item.id,
            session_number=item.session_number,
            location_id=item.location_id,
            scope_type=item.scope_type,
            status=item.status,
            planned_start_at=item.planned_start_at,
            planned_end_at=item.planned_end_at,
            started_at=item.started_at,
            completed_at=item.completed_at,
            created_by=item.created_by,
            approved_by=item.approved_by,
            approved_at=item.approved_at,
            notes=item.notes,
            location=AssetLocationRead.model_validate(item.location),
            expected_item_count=len(expected_items),
            result_count=len(results),
            expected_items=expected_items,
            results=results,
        )


class StocktakeSessionListItemRead(BaseModel):
    id: UUID
    session_number: str
    location_id: UUID
    scope_type: str
    status: str
    planned_start_at: datetime
    planned_end_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_by: UUID | None
    approved_by: UUID | None
    approved_at: datetime | None
    notes: str | None
    expected_item_count: int
    result_count: int
    location: AssetLocationRead

    @classmethod
    def from_model(cls, item: object) -> StocktakeSessionListItemRead:
        return cls(
            id=item.id,
            session_number=item.session_number,
            location_id=item.location_id,
            scope_type=item.scope_type,
            status=item.status,
            planned_start_at=item.planned_start_at,
            planned_end_at=item.planned_end_at,
            started_at=item.started_at,
            completed_at=item.completed_at,
            created_by=item.created_by,
            approved_by=item.approved_by,
            approved_at=item.approved_at,
            notes=item.notes,
            expected_item_count=len(getattr(item, "expected_items", [])),
            result_count=len(getattr(item, "results", [])),
            location=AssetLocationRead.model_validate(item.location),
        )


class LocationDiscrepancyReportItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    scan_event_id: UUID
    expected_location_id: UUID | None
    observed_location_id: UUID | None
    verification_result: str
    verified_at: datetime
    verified_by: UUID | None
    resolution_status: str
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution_action: str | None
    notes: str | None
    asset: TrackingAssetReferenceRead | None = None
    expected_location: AssetLocationRead | None = None
    observed_location: AssetLocationRead | None = None


class MissingAssetReportItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stocktake_session_id: UUID
    asset_id: UUID | None
    result_type: str
    observed_location_id: UUID | None
    observed_at: datetime | None
    resolution_status: str
    resolution_reference_type: str | None
    resolution_reference_id: UUID | None
    notes: str | None
    created_at: datetime
    asset: TrackingAssetReferenceRead | None = None
    stocktake_session: StocktakeSessionListItemRead | None = None


class UnverifiedAssetReportItemRead(BaseModel):
    id: UUID
    asset_code: str
    asset_name: str
    asset_status: str
    condition_status: str
    tracking_status: str
    tag_number: str | None
    serial_number: str | None
    current_location_id: UUID | None
    current_location: AssetLocationRead | None
    last_verified_at: datetime | None
    last_verified_location_id: UUID | None
    verification_age_days: int | None

    @classmethod
    def from_model(
        cls,
        asset: object,
        *,
        verification_age_days: int | None,
    ) -> UnverifiedAssetReportItemRead:
        return cls(
            id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            asset_status=asset.asset_status,
            condition_status=asset.condition_status,
            tracking_status=asset.tracking_status,
            tag_number=asset.tag_number,
            serial_number=asset.serial_number,
            current_location_id=asset.current_location_id,
            current_location=(
                AssetLocationRead.model_validate(asset.current_location)
                if getattr(asset, "current_location", None)
                else None
            ),
            last_verified_at=asset.last_verified_at,
            last_verified_location_id=asset.last_verified_location_id,
            verification_age_days=verification_age_days,
        )
