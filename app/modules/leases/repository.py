from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.leases.models import AssetLeaseContract, AssetLeaseItem, AssetLeasePayment
from app.shared.pagination import PaginationParams


class LeaseContractRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetLeaseContract) -> AssetLeaseContract:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["items", "payments"])
        return item

    async def get(self, contract_id: UUID) -> AssetLeaseContract | None:
        stmt = (
            select(AssetLeaseContract)
            .options(
                selectinload(AssetLeaseContract.items).selectinload(AssetLeaseItem.asset),
                selectinload(AssetLeaseContract.payments),
            )
            .where(AssetLeaseContract.id == contract_id)
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        pagination: PaginationParams,
    ) -> tuple[Sequence[AssetLeaseContract], int]:
        stmt: Select[tuple[AssetLeaseContract]] = select(AssetLeaseContract).options(
            selectinload(AssetLeaseContract.items),
            selectinload(AssetLeaseContract.payments),
        )
        count_stmt = select(func.count()).select_from(AssetLeaseContract)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            stmt = stmt.where(AssetLeaseContract.contract_number.ilike(search_value))
            count_stmt = count_stmt.where(AssetLeaseContract.contract_number.ilike(search_value))
        sort_column = getattr(AssetLeaseContract, pagination.sort or "contract_number")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items


class LeaseItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetLeaseItem) -> AssetLeaseItem:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["asset"])
        return item

    async def list_by_contract(self, contract_id: UUID) -> Sequence[AssetLeaseItem]:
        stmt = (
            select(AssetLeaseItem)
            .options(selectinload(AssetLeaseItem.asset))
            .where(AssetLeaseItem.lease_contract_id == contract_id)
            .order_by(AssetLeaseItem.lease_start_date.asc())
        )
        items = await self.session.scalars(stmt)
        return items.all()

    async def list_active_overlaps(
        self,
        asset_id: UUID,
        *,
        lease_start_date: date,
        lease_end_date: date,
    ) -> Sequence[AssetLeaseItem]:
        stmt = (
            select(AssetLeaseItem)
            .options(selectinload(AssetLeaseItem.lease_contract))
            .where(
                AssetLeaseItem.asset_id == asset_id,
                AssetLeaseItem.returned_at.is_(None),
                AssetLeaseItem.lease_start_date <= lease_end_date,
                AssetLeaseItem.lease_end_date >= lease_start_date,
            )
        )
        items = await self.session.scalars(stmt)
        return items.all()


class LeasePaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AssetLeasePayment) -> AssetLeasePayment:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_contract(self, contract_id: UUID) -> Sequence[AssetLeasePayment]:
        stmt = (
            select(AssetLeasePayment)
            .where(AssetLeasePayment.lease_contract_id == contract_id)
            .order_by(AssetLeasePayment.period_start.asc())
        )
        items = await self.session.scalars(stmt)
        return items.all()
