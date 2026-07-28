from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_session,
    require_asset_read,
    require_asset_write,
    require_maintenance_read,
)
from app.modules.assets.schemas import (
    AssetAssignmentCreate,
    AssetAssignmentRead,
    AssetAssignmentReturnPayload,
    AssetAttributeDefinitionCreate,
    AssetAttributeDefinitionRead,
    AssetAttributeValueCreate,
    AssetAttributeValueRead,
    AssetCategoryCreate,
    AssetCategoryRead,
    AssetClassCreate,
    AssetClassRead,
    AssetComponentChangeCreate,
    AssetComponentHistoryRead,
    AssetComponentRead,
    AssetCreate,
    AssetLifecycleReviewCreate,
    AssetLifecycleReviewRead,
    AssetLocationChangeCreate,
    AssetLocationCreate,
    AssetLocationHistoryRead,
    AssetLocationRead,
    AssetOwnershipCreate,
    AssetOwnershipRead,
    AssetRead,
    AssetRetirementApprovePayload,
    AssetRetirementConfirmPayload,
    AssetRetirementRead,
    AssetRetirementRequestCreate,
    AssetStatusChangeCreate,
    AssetStatusHistoryRead,
    AssetTimelineEventRead,
    AssetTransferActionPayload,
    AssetTransferCreate,
    AssetTransferListItemRead,
    AssetTransferRead,
    AssetUpdate,
)
from app.modules.assets.service import AssetRegistryService
from app.modules.auth.models import AppUser
from app.modules.maintenance.service import MaintenanceService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter()


@router.post(
    "/asset-categories",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_category(
    request: Request,
    payload: AssetCategoryCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    category = await service.create_category(payload)
    return success_response(
        request=request,
        message="Asset category berhasil dibuat.",
        data=AssetCategoryRead.model_validate(category).model_dump(mode="json"),
    )


@router.get("/asset-categories", dependencies=[Depends(require_asset_read)])
async def list_asset_categories(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_categories()
    return success_response(
        request=request,
        message="Daftar asset category berhasil diambil.",
        data=[
            AssetCategoryRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/asset-classes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_class(
    request: Request,
    payload: AssetClassCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    asset_class = await service.create_class(payload)
    return success_response(
        request=request,
        message="Asset class berhasil dibuat.",
        data=AssetClassRead.model_validate(asset_class).model_dump(mode="json"),
    )


@router.get("/asset-classes", dependencies=[Depends(require_asset_read)])
async def list_asset_classes(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_classes()
    return success_response(
        request=request,
        message="Daftar asset class berhasil diambil.",
        data=[
            AssetClassRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/asset-locations",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_location(
    request: Request,
    payload: AssetLocationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    location = await service.create_location(payload)
    return success_response(
        request=request,
        message="Asset location berhasil dibuat.",
        data=AssetLocationRead.model_validate(location).model_dump(mode="json"),
    )


@router.post(
    "/asset-attribute-definitions",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_attribute_definition(
    request: Request,
    payload: AssetAttributeDefinitionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_attribute_definition(payload)
    return success_response(
        request=request,
        message="Asset attribute definition berhasil dibuat.",
        data=AssetAttributeDefinitionRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/asset-categories/{asset_category_id}/attribute-definitions",
    dependencies=[Depends(require_asset_read)],
)
async def list_asset_attribute_definitions(
    request: Request,
    asset_category_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_attribute_definitions(asset_category_id)
    return success_response(
        request=request,
        message="Daftar asset attribute definition berhasil diambil.",
        data=[
            AssetAttributeDefinitionRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.get("/asset-locations", dependencies=[Depends(require_asset_read)])
async def list_asset_locations(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_locations()
    return success_response(
        request=request,
        message="Daftar asset location berhasil diambil.",
        data=[AssetLocationRead.model_validate(item).model_dump(mode="json") for item in items],
    )


@router.post(
    "/assets",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset(
    request: Request,
    payload: AssetCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    asset = await service.create_asset(
        payload.model_copy(
            update={
                "created_by": current_user.id,
                "updated_by": current_user.id,
            }
        )
    )
    return success_response(
        request=request,
        message="Asset berhasil dibuat.",
        data=AssetRead.from_model(asset).model_dump(mode="json"),
    )


@router.post(
    "/asset-transfers",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_transfer(
    request: Request,
    payload: AssetTransferCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_transfer(
        payload.model_copy(update={"requested_by": current_user.id})
    )
    return success_response(
        request=request,
        message="Asset transfer berhasil dibuat.",
        data=AssetTransferRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/asset-transfers", dependencies=[Depends(require_asset_read)])
async def list_asset_transfers(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="transfer_date",
        pattern="^(transfer_number|transfer_date|status|movement_purpose|approved_at|received_at)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    status_filter: str | None = Query(default=None, alias="status"),
    to_location_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> dict:
    service = AssetRegistryService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_transfers(
        pagination,
        status_filter=status_filter,
        to_location_id=to_location_id,
        requested_by=requested_by,
    )
    return success_response(
        request=request,
        message="Daftar asset transfer berhasil diambil.",
        data=[
            AssetTransferListItemRead(
                id=item.id,
                transfer_number=item.transfer_number,
                transfer_date=item.transfer_date,
                transfer_type=item.transfer_type,
                status=item.status,
                movement_purpose=item.movement_purpose,
                is_permanent=item.is_permanent,
                from_location_id=item.from_location_id,
                to_location_id=item.to_location_id,
                requested_by=item.requested_by,
                approved_by=item.approved_by,
                approved_at=item.approved_at,
                received_at=item.received_at,
                reason=item.reason,
                from_location=(
                    AssetLocationRead.model_validate(item.from_location)
                    if item.from_location
                    else None
                ),
                to_location=AssetLocationRead.model_validate(item.to_location),
                item_count=len(item.items),
            ).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/asset-transfers/{transfer_id}", dependencies=[Depends(require_asset_read)])
async def get_asset_transfer(
    request: Request,
    transfer_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.get_transfer(transfer_id)
    return success_response(
        request=request,
        message="Detail asset transfer berhasil diambil.",
        data=AssetTransferRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/asset-transfers/{transfer_id}/submit",
    dependencies=[Depends(require_asset_write)],
)
async def submit_asset_transfer(
    request: Request,
    transfer_id: UUID,
    payload: AssetTransferActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.submit_transfer(
        transfer_id,
        payload.model_copy(update={"actor_id": current_user.id}),
    )
    return success_response(
        request=request,
        message="Asset transfer berhasil disubmit.",
        data=AssetTransferRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/asset-transfers/{transfer_id}/approve",
    dependencies=[Depends(require_asset_write)],
)
async def approve_asset_transfer(
    request: Request,
    transfer_id: UUID,
    payload: AssetTransferActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.approve_transfer(
        transfer_id,
        payload.model_copy(update={"actor_id": current_user.id}),
    )
    return success_response(
        request=request,
        message="Asset transfer berhasil diapprove.",
        data=AssetTransferRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/asset-transfers/{transfer_id}/complete",
    dependencies=[Depends(require_asset_write)],
)
async def complete_asset_transfer(
    request: Request,
    transfer_id: UUID,
    payload: AssetTransferActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.complete_transfer(
        transfer_id,
        payload.model_copy(update={"actor_id": current_user.id}),
    )
    return success_response(
        request=request,
        message="Asset transfer berhasil diselesaikan.",
        data=AssetTransferRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets", dependencies=[Depends(require_asset_read)])
async def list_assets(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="asset_code",
        pattern="^(asset_code|asset_name|asset_status|created_at)$",
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> dict:
    service = AssetRegistryService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_assets(pagination)
    return success_response(
        request=request,
        message="Daftar asset berhasil diambil.",
        data=[AssetRead.from_model(item).model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/assets/{asset_id}", dependencies=[Depends(require_asset_read)])
async def get_asset(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    asset = await service.get_asset(asset_id)
    return success_response(
        request=request,
        message="Detail asset berhasil diambil.",
        data=AssetRead.from_model(asset).model_dump(mode="json"),
    )


@router.patch("/assets/{asset_id}", dependencies=[Depends(require_asset_write)])
async def update_asset(
    request: Request,
    asset_id: UUID,
    payload: AssetUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    asset = await service.update_asset(
        asset_id,
        payload.model_copy(update={"updated_by": current_user.id}),
    )
    return success_response(
        request=request,
        message="Asset berhasil diperbarui.",
        data=AssetRead.from_model(asset).model_dump(mode="json"),
    )


@router.post(
    "/assets/{asset_id}/location-changes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_location_change(
    request: Request,
    asset_id: UUID,
    payload: AssetLocationChangeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.record_location_change(
        asset_id,
        payload.model_copy(update={"recorded_by": current_user.id}),
    )
    return success_response(
        request=request,
        message="Perubahan lokasi asset berhasil dicatat.",
        data=AssetLocationHistoryRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets/{asset_id}/location-history", dependencies=[Depends(require_asset_read)])
async def get_asset_location_history(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_location_history(asset_id)
    return success_response(
        request=request,
        message="Riwayat lokasi asset berhasil diambil.",
        data=[
            AssetLocationHistoryRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/assets/{asset_id}/assignments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_assignment(
    request: Request,
    asset_id: UUID,
    payload: AssetAssignmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_assignment(asset_id, payload)
    return success_response(
        request=request,
        message="Assignment asset berhasil dibuat.",
        data=AssetAssignmentRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/assignments/{assignment_id}/return",
    dependencies=[Depends(require_asset_write)],
)
async def return_asset_assignment(
    request: Request,
    assignment_id: UUID,
    payload: AssetAssignmentReturnPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.return_assignment(assignment_id, payload)
    return success_response(
        request=request,
        message="Assignment asset berhasil dikembalikan.",
        data=AssetAssignmentRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/assets/{asset_id}/attribute-values",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def upsert_asset_attribute_value(
    request: Request,
    asset_id: UUID,
    payload: AssetAttributeValueCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.upsert_attribute_value(asset_id, payload)
    return success_response(
        request=request,
        message="Nilai attribute asset berhasil disimpan.",
        data=AssetAttributeValueRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets/{asset_id}/attribute-values", dependencies=[Depends(require_asset_read)])
async def get_asset_attribute_values(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_attribute_values(asset_id)
    return success_response(
        request=request,
        message="Daftar nilai attribute asset berhasil diambil.",
        data=[
            AssetAttributeValueRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/assets/{asset_id}/ownerships",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_ownership(
    request: Request,
    asset_id: UUID,
    payload: AssetOwnershipCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_ownership(asset_id, payload)
    return success_response(
        request=request,
        message="Ownership asset berhasil dibuat.",
        data=AssetOwnershipRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets/{asset_id}/ownerships", dependencies=[Depends(require_asset_read)])
async def get_asset_ownerships(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_ownerships(asset_id)
    return success_response(
        request=request,
        message="Daftar ownership asset berhasil diambil.",
        data=[AssetOwnershipRead.model_validate(item).model_dump(mode="json") for item in items],
    )


@router.get("/assets/{asset_id}/assignment-history", dependencies=[Depends(require_asset_read)])
async def get_asset_assignment_history(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_assignment_history(asset_id)
    return success_response(
        request=request,
        message="Riwayat assignment asset berhasil diambil.",
        data=[AssetAssignmentRead.model_validate(item).model_dump(mode="json") for item in items],
    )


@router.post(
    "/assets/{asset_id}/components",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def change_asset_components(
    request: Request,
    asset_id: UUID,
    payload: AssetComponentChangeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.change_components(
        asset_id,
        payload,
        changed_by=current_user.id,
    )
    return success_response(
        request=request,
        message="Perubahan komponen asset berhasil dicatat.",
        data=AssetComponentHistoryRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets/{asset_id}/components", dependencies=[Depends(require_asset_read)])
async def list_asset_components(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_components(asset_id)
    return success_response(
        request=request,
        message="Daftar komponen asset berhasil diambil.",
        data=[AssetComponentRead.from_model(item).model_dump(mode="json") for item in items],
    )


@router.get(
    "/assets/{asset_id}/component-history",
    dependencies=[Depends(require_asset_read)],
)
async def list_asset_component_history(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_component_history(asset_id)
    return success_response(
        request=request,
        message="Riwayat komponen asset berhasil diambil.",
        data=[
            AssetComponentHistoryRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/assets/{asset_id}/status-changes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_status_change(
    request: Request,
    asset_id: UUID,
    payload: AssetStatusChangeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_status_change(
        asset_id,
        payload.model_copy(update={"changed_by": current_user.id}),
    )
    return success_response(
        request=request,
        message="Perubahan status asset berhasil dicatat.",
        data=AssetStatusHistoryRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets/{asset_id}/status-history", dependencies=[Depends(require_asset_read)])
async def get_asset_status_history(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_status_history(asset_id)
    return success_response(
        request=request,
        message="Riwayat status asset berhasil diambil.",
        data=[
            AssetStatusHistoryRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/assets/{asset_id}/lifecycle-reviews",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_lifecycle_review(
    request: Request,
    asset_id: UUID,
    payload: AssetLifecycleReviewCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_lifecycle_review(
        asset_id,
        payload,
        reviewed_by=current_user.id,
    )
    return success_response(
        request=request,
        message="Lifecycle review asset berhasil dibuat.",
        data=AssetLifecycleReviewRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/assets/{asset_id}/lifecycle-reviews",
    dependencies=[Depends(require_asset_read)],
)
async def list_asset_lifecycle_reviews(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_lifecycle_reviews(asset_id)
    return success_response(
        request=request,
        message="Daftar lifecycle review asset berhasil diambil.",
        data=[
            AssetLifecycleReviewRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/assets/{asset_id}/retirement-requests",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_asset_retirement_request(
    request: Request,
    asset_id: UUID,
    payload: AssetRetirementRequestCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.create_retirement_request(asset_id, payload)
    return success_response(
        request=request,
        message="Retirement request asset berhasil dibuat.",
        data=AssetRetirementRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/assets/{asset_id}/retirement-requests",
    dependencies=[Depends(require_asset_read)],
)
async def list_asset_retirement_requests(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.list_retirement_requests(asset_id)
    return success_response(
        request=request,
        message="Daftar retirement request asset berhasil diambil.",
        data=[AssetRetirementRead.model_validate(item).model_dump(mode="json") for item in items],
    )


@router.get(
    "/retirement-requests/{retirement_id}",
    dependencies=[Depends(require_asset_read)],
)
async def get_asset_retirement_request(
    request: Request,
    retirement_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.get_retirement_request(retirement_id)
    return success_response(
        request=request,
        message="Detail retirement request asset berhasil diambil.",
        data=AssetRetirementRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/retirement-requests/{retirement_id}/approve",
    dependencies=[Depends(require_asset_write)],
)
async def approve_asset_retirement_request(
    request: Request,
    retirement_id: UUID,
    payload: AssetRetirementApprovePayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.approve_retirement_request(
        retirement_id,
        approved_by=payload.approved_by or current_user.id,
    )
    return success_response(
        request=request,
        message="Retirement request asset berhasil diapprove.",
        data=AssetRetirementRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/retirement-requests/{retirement_id}/confirm",
    dependencies=[Depends(require_asset_write)],
)
async def confirm_asset_retirement_request(
    request: Request,
    retirement_id: UUID,
    payload: AssetRetirementConfirmPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AssetRegistryService(session)
    item = await service.confirm_retirement_request(
        retirement_id,
        payload,
        changed_by=current_user.id,
    )
    return success_response(
        request=request,
        message="Retirement request asset berhasil dikonfirmasi.",
        data=AssetRetirementRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/assets/{asset_id}/timeline", dependencies=[Depends(require_asset_read)])
async def get_asset_timeline(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AssetRegistryService(session)
    items = await service.get_timeline(asset_id)
    return success_response(
        request=request,
        message="Timeline asset berhasil diambil.",
        data=[
            AssetTimelineEventRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.get(
    "/assets/{asset_id}/maintenance-history",
    dependencies=[Depends(require_maintenance_read)],
)
async def get_asset_maintenance_history(
    request: Request,
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.get_asset_maintenance_history(asset_id)
    return success_response(
        request=request,
        message="Riwayat maintenance asset berhasil diambil.",
        data=[item.model_dump(mode="json") for item in items],
    )
