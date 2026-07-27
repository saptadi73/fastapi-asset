from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_session,
    require_tracking_read,
    require_tracking_report_read,
    require_tracking_write,
)
from app.modules.auth.models import AppUser
from app.modules.tracking.schemas import (
    AssetScanEventCreate,
    AssetScanEventRead,
    AssetTrackingTimelineRead,
    StocktakeActionPayload,
    StocktakeSessionCreate,
    StocktakeSessionListItemRead,
    StocktakeSessionRead,
)
from app.modules.tracking.service import AssetTrackingService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter()


@router.post(
    "/tracking/scan-events",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tracking_write)],
)
async def create_scan_event(
    request: Request,
    payload: AssetScanEventCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.create_scan_event(
        payload.model_copy(update={"scanned_by": current_user.id})
    )
    return success_response(
        request=request,
        message="Scan event berhasil dicatat.",
        data=AssetScanEventRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.post(
    "/tracking/scan-events/batch",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tracking_write)],
)
async def create_scan_event_batch(
    request: Request,
    payload: list[AssetScanEventCreate],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    items = await service.create_scan_event_batch(
        [item.model_copy(update={"scanned_by": current_user.id}) for item in payload]
    )
    return success_response(
        request=request,
        message="Batch scan event berhasil diproses.",
        data=[
            AssetScanEventRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in items
        ],
    )


@router.get("/assets/{asset_id}/tracking", dependencies=[Depends(require_tracking_read)])
async def get_asset_tracking(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.get_asset_tracking(asset_id)
    return success_response(
        request=request,
        message="Riwayat tracking asset berhasil diambil.",
        data=AssetTrackingTimelineRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.post(
    "/stocktakes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tracking_write)],
)
async def create_stocktake_session(
    request: Request,
    payload: StocktakeSessionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.create_stocktake_session(
        payload.model_copy(update={"created_by": current_user.id})
    )
    return success_response(
        request=request,
        message="Stocktake session berhasil dibuat.",
        data=StocktakeSessionRead.from_model(item).model_dump(mode="json"),
    )


@router.get("/stocktakes", dependencies=[Depends(require_tracking_read)])
async def list_stocktake_sessions(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="planned_start_at",
        pattern="^(session_number|planned_start_at|status|started_at|completed_at)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    status_filter: str | None = Query(default=None, alias="status"),
    location_id: UUID | None = None,
) -> dict:
    service = AssetTrackingService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_stocktake_sessions(
        pagination,
        status_filter=status_filter,
        location_id=location_id,
    )
    return success_response(
        request=request,
        message="Daftar stocktake session berhasil diambil.",
        data=[
            StocktakeSessionListItemRead.from_model(item).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get(
    "/stocktakes/{stocktake_session_id}",
    dependencies=[Depends(require_tracking_read)],
)
async def get_stocktake_session(
    request: Request,
    stocktake_session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.get_stocktake_session(stocktake_session_id)
    return success_response(
        request=request,
        message="Detail stocktake session berhasil diambil.",
        data=StocktakeSessionRead.from_model(item).model_dump(mode="json"),
    )


@router.post(
    "/stocktakes/{stocktake_session_id}/start",
    dependencies=[Depends(require_tracking_write)],
)
async def start_stocktake_session(
    request: Request,
    stocktake_session_id: UUID,
    payload: StocktakeActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.start_stocktake(
        stocktake_session_id,
        payload.model_copy(update={"actor_id": current_user.id}),
    )
    return success_response(
        request=request,
        message="Stocktake session berhasil dimulai.",
        data=StocktakeSessionRead.from_model(item).model_dump(mode="json"),
    )


@router.post(
    "/stocktakes/{stocktake_session_id}/scan",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tracking_write)],
)
async def scan_stocktake_session(
    request: Request,
    stocktake_session_id: UUID,
    payload: AssetScanEventCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.scan_stocktake(
        stocktake_session_id,
        payload.model_copy(update={"scanned_by": current_user.id}),
    )
    return success_response(
        request=request,
        message="Scan stocktake berhasil dicatat.",
        data=AssetScanEventRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.post(
    "/stocktakes/{stocktake_session_id}/complete",
    dependencies=[Depends(require_tracking_write)],
)
async def complete_stocktake_session(
    request: Request,
    stocktake_session_id: UUID,
    payload: StocktakeActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.complete_stocktake(
        stocktake_session_id,
        payload.model_copy(update={"actor_id": current_user.id}),
    )
    return success_response(
        request=request,
        message="Stocktake session berhasil diselesaikan.",
        data=StocktakeSessionRead.from_model(item).model_dump(mode="json"),
    )


@router.post(
    "/stocktakes/{stocktake_session_id}/approve",
    dependencies=[Depends(require_tracking_write)],
)
async def approve_stocktake_session(
    request: Request,
    stocktake_session_id: UUID,
    payload: StocktakeActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetTrackingService(session)
    item = await service.approve_stocktake(
        stocktake_session_id,
        payload.model_copy(update={"actor_id": current_user.id}),
    )
    return success_response(
        request=request,
        message="Stocktake session berhasil diapprove.",
        data=StocktakeSessionRead.from_model(item).model_dump(mode="json"),
    )


@router.get(
    "/reports/location-discrepancies",
    dependencies=[Depends(require_tracking_report_read)],
)
async def get_location_discrepancies_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="verified_at",
        pattern="^(verified_at|resolution_status)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    resolution_status: str | None = None,
    location_id: UUID | None = None,
) -> dict:
    service = AssetTrackingService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.get_location_discrepancies_report(
        pagination,
        resolution_status=resolution_status,
        location_id=location_id,
    )
    return success_response(
        request=request,
        message="Report discrepancy lokasi berhasil diambil.",
        data=[item.model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get(
    "/reports/missing-assets",
    dependencies=[Depends(require_tracking_report_read)],
)
async def get_missing_assets_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="created_at",
        pattern="^(created_at|resolution_status|result_type)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    stocktake_session_id: UUID | None = None,
    resolution_status: str | None = None,
    location_id: UUID | None = None,
) -> dict:
    service = AssetTrackingService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.get_missing_assets_report(
        pagination,
        stocktake_session_id=stocktake_session_id,
        location_id=location_id,
        resolution_status=resolution_status,
    )
    return success_response(
        request=request,
        message="Report aset hilang dari stocktake berhasil diambil.",
        data=[item.model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get(
    "/reports/unverified-assets",
    dependencies=[Depends(require_tracking_report_read)],
)
async def get_unverified_assets_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="last_verified_at",
        pattern="^(last_verified_at|asset_code|asset_name)$",
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    days_since_verified: int = Query(default=30, ge=1, le=3650),
    location_id: UUID | None = None,
) -> dict:
    service = AssetTrackingService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.get_unverified_assets_report(
        pagination,
        days_since_verified=days_since_verified,
        location_id=location_id,
    )
    return success_response(
        request=request,
        message="Report aset belum diverifikasi berhasil diambil.",
        data=[item.model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )
