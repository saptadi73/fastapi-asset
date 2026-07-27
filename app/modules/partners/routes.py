from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_partner_read, require_partner_write
from app.modules.partners.schemas import BusinessPartnerCreate, BusinessPartnerRead
from app.modules.partners.service import BusinessPartnerService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter(prefix="/business-partners")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_partner_write)],
)
async def create_business_partner(
    request: Request,
    payload: BusinessPartnerCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = BusinessPartnerService(session)
    partner = await service.create(payload)
    return success_response(
        request=request,
        message="Business partner berhasil dibuat.",
        data=BusinessPartnerRead.model_validate(partner).model_dump(mode="json"),
    )


@router.get("", dependencies=[Depends(require_partner_read)])
async def list_business_partners(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(default="partner_code", pattern="^(partner_code|partner_name|created_at)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> dict:
    service = BusinessPartnerService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    partners, total_items = await service.list(pagination)
    return success_response(
        request=request,
        message="Daftar business partner berhasil diambil.",
        data=[
            BusinessPartnerRead.model_validate(item).model_dump(mode="json")
            for item in partners
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/{partner_id}", dependencies=[Depends(require_partner_read)])
async def get_business_partner(
    request: Request,
    partner_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = BusinessPartnerService(session)
    partner = await service.get(str(partner_id))
    return success_response(
        request=request,
        message="Detail business partner berhasil diambil.",
        data=BusinessPartnerRead.model_validate(partner).model_dump(mode="json"),
    )
