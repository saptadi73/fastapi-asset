from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_asset_read, require_asset_write
from app.modules.software_licenses.schemas import (
    SoftwareLicenseAssignmentCreate,
    SoftwareLicenseAssignmentRead,
    SoftwareLicenseAssignmentReleasePayload,
    SoftwareLicenseCreate,
    SoftwareLicenseListItemRead,
    SoftwareLicenseRead,
    SoftwareProductCreate,
    SoftwareProductRead,
)
from app.modules.software_licenses.service import SoftwareLicenseService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter()


@router.post(
    "/software-products",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_software_product(
    request: Request,
    payload: SoftwareProductCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = SoftwareLicenseService(session)
    item = await service.create_product(payload)
    return success_response(
        request=request,
        message="Software product berhasil dibuat.",
        data=SoftwareProductRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/software-products", dependencies=[Depends(require_asset_read)])
async def list_software_products(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = SoftwareLicenseService(session)
    items = await service.list_products()
    return success_response(
        request=request,
        message="Daftar software product berhasil diambil.",
        data=[SoftwareProductRead.model_validate(item).model_dump(mode="json") for item in items],
    )


@router.post(
    "/software-licenses",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def create_software_license(
    request: Request,
    payload: SoftwareLicenseCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = SoftwareLicenseService(session)
    item = await service.create_license(payload)
    return success_response(
        request=request,
        message="Software license berhasil dibuat.",
        data=SoftwareLicenseRead.from_model(item, as_of=date(2026, 7, 27)).model_dump(mode="json"),
    )

@router.get("/software-licenses", dependencies=[Depends(require_asset_read)])
async def list_software_licenses(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(default="expiry_date", pattern="^(expiry_date|license_number|status)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> dict:
    service = SoftwareLicenseService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_licenses(pagination)
    return success_response(
        request=request,
        message="Daftar software license berhasil diambil.",
        data=[
            SoftwareLicenseListItemRead.from_model(item, as_of=date(2026, 7, 27)).model_dump(
                mode="json"
            )
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/software-licenses/{license_id}", dependencies=[Depends(require_asset_read)])
async def get_software_license(
    request: Request,
    license_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = SoftwareLicenseService(session)
    item = await service.get_license(license_id)
    return success_response(
        request=request,
        message="Detail software license berhasil diambil.",
        data=SoftwareLicenseRead.from_model(item, as_of=date(2026, 7, 27)).model_dump(mode="json"),
    )


@router.post(
    "/software-licenses/{license_id}/assignments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def assign_software_license(
    request: Request,
    license_id: UUID,
    payload: SoftwareLicenseAssignmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = SoftwareLicenseService(session)
    item = await service.assign_license(license_id, payload)
    return success_response(
        request=request,
        message="Software license assignment berhasil dicatat.",
        data=SoftwareLicenseRead.from_model(item, as_of=date(2026, 7, 27)).model_dump(mode="json"),
    )


@router.post(
    "/software-license-assignments/{assignment_id}/release",
    dependencies=[Depends(require_asset_write)],
)
async def release_software_license_assignment(
    request: Request,
    assignment_id: UUID,
    payload: SoftwareLicenseAssignmentReleasePayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = SoftwareLicenseService(session)
    item = await service.release_assignment(assignment_id, payload)
    return success_response(
        request=request,
        message="Software license assignment berhasil direlease.",
        data=SoftwareLicenseAssignmentRead.from_model(item).model_dump(mode="json"),
    )
