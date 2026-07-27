from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.partners.models import BusinessPartner
from app.shared.pagination import PaginationParams


class BusinessPartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, partner: BusinessPartner) -> BusinessPartner:
        self.session.add(partner)
        await self.session.flush()
        await self.session.refresh(partner, attribute_names=["roles"])
        return partner

    async def get(self, partner_id: UUID) -> BusinessPartner | None:
        stmt = (
            select(BusinessPartner)
            .options(selectinload(BusinessPartner.roles))
            .where(BusinessPartner.id == partner_id)
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        pagination: PaginationParams,
    ) -> tuple[Sequence[BusinessPartner], int]:
        stmt: Select[tuple[BusinessPartner]] = select(BusinessPartner).options(
            selectinload(BusinessPartner.roles)
        )
        count_stmt = select(func.count()).select_from(BusinessPartner)

        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                BusinessPartner.partner_code.ilike(search_value),
                BusinessPartner.partner_name.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        sort_column = getattr(BusinessPartner, pagination.sort or "partner_code")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)

        result = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return result.all(), total_items
