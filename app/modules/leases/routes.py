from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_asset_read, require_asset_write
from app.modules.leases.schemas import (
    LeaseContractAssetCreate,
    LeaseContractAssetRead,
    LeaseContractCreate,
    LeaseContractListItemRead,
    LeaseContractRead,
    LeasePaymentCreate,
    LeasePaymentRead,
)
from app.modules.leases.service import LeaseService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter(prefix="/lease-contracts")


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_asset_write)])
async def create_lease_contract(
    request: Request,
    payload: LeaseContractCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = LeaseService(session)
    item = await service.create_contract(payload)
    return success_response(
        request=request,
        message="Lease contract berhasil dibuat.",
        data=LeaseContractRead.from_model(item).model_dump(mode="json"),
    )


@router.get("", dependencies=[Depends(require_asset_read)])
async def list_lease_contracts(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="contract_number",
        pattern="^(contract_number|start_date|end_date|status)$",
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> dict:
    service = LeaseService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_contracts(pagination)
    return success_response(
        request=request,
        message="Daftar lease contract berhasil diambil.",
        data=[LeaseContractListItemRead.from_model(item).model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/{contract_id}", dependencies=[Depends(require_asset_read)])
async def get_lease_contract(
    request: Request,
    contract_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = LeaseService(session)
    item = await service.get_contract(contract_id)
    return success_response(
        request=request,
        message="Detail lease contract berhasil diambil.",
        data=LeaseContractRead.from_model(item).model_dump(mode="json"),
    )


@router.post(
    "/{contract_id}/assets",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def add_lease_contract_asset(
    request: Request,
    contract_id: UUID,
    payload: LeaseContractAssetCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = LeaseService(session)
    item = await service.add_contract_asset(contract_id, payload)
    return success_response(
        request=request,
        message="Asset lease item berhasil ditambahkan ke contract.",
        data=LeaseContractRead.from_model(item).model_dump(mode="json"),
    )


@router.get("/{contract_id}/assets", dependencies=[Depends(require_asset_read)])
async def list_lease_contract_assets(
    request: Request,
    contract_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = LeaseService(session)
    items = await service.list_contract_assets(contract_id)
    return success_response(
        request=request,
        message="Daftar asset lease item berhasil diambil.",
        data=[LeaseContractAssetRead.from_model(item).model_dump(mode="json") for item in items],
    )


@router.post(
    "/{contract_id}/payments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_asset_write)],
)
async def add_lease_contract_payment(
    request: Request,
    contract_id: UUID,
    payload: LeasePaymentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = LeaseService(session)
    item = await service.add_payment(contract_id, payload)
    return success_response(
        request=request,
        message="Lease payment berhasil dicatat.",
        data=LeaseContractRead.from_model(item).model_dump(mode="json"),
    )


@router.get("/{contract_id}/payments", dependencies=[Depends(require_asset_read)])
async def list_lease_contract_payments(
    request: Request,
    contract_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = LeaseService(session)
    items = await service.list_payments(contract_id)
    return success_response(
        request=request,
        message="Daftar lease payment berhasil diambil.",
        data=[LeasePaymentRead.model_validate(item).model_dump(mode="json") for item in items],
    )
