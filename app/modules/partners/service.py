from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.partners.exceptions import BusinessPartnerNotFoundError
from app.modules.partners.models import BusinessPartner, BusinessPartnerRole
from app.modules.partners.repository import BusinessPartnerRepository
from app.modules.partners.schemas import BusinessPartnerCreate
from app.shared.pagination import PaginationParams


class BusinessPartnerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = BusinessPartnerRepository(session)

    async def create(self, payload: BusinessPartnerCreate) -> BusinessPartner:
        partner = BusinessPartner(
            partner_code=payload.partner_code,
            partner_name=payload.partner_name,
            tax_number=payload.tax_number,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
            address=payload.address,
            sap_card_code=payload.sap_card_code,
            is_active=payload.is_active,
            roles=[
                BusinessPartnerRole(
                    role_type=role.role_type.value,
                    valid_from=role.valid_from,
                    valid_to=role.valid_to,
                )
                for role in payload.roles
            ],
        )

        try:
            async with self.session.begin():
                return await self.repository.create(partner)
        except IntegrityError as exc:
            raise AppError(
                code="BUSINESS_PARTNER_CONFLICT",
                message="Partner code sudah digunakan.",
                status_code=409,
            ) from exc

    async def get(self, partner_id: str) -> BusinessPartner:
        partner = await self.repository.get(partner_id)
        if partner is None:
            raise BusinessPartnerNotFoundError(str(partner_id))
        return partner

    async def list(self, pagination: PaginationParams) -> tuple[list[BusinessPartner], int]:
        items, total_items = await self.repository.list(pagination)
        return list(items), total_items
