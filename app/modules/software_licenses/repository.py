from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.software_licenses.models import (
    SoftwareLicense,
    SoftwareLicenseAssignment,
    SoftwareProduct,
)
from app.shared.pagination import PaginationParams


class SoftwareProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: SoftwareProduct) -> SoftwareProduct:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, product_id: UUID) -> SoftwareProduct | None:
        return await self.session.get(SoftwareProduct, product_id)

    async def list(self) -> Sequence[SoftwareProduct]:
        result = await self.session.scalars(
            select(SoftwareProduct).order_by(SoftwareProduct.product_code.asc())
        )
        return result.all()


class SoftwareLicenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: SoftwareLicense) -> SoftwareLicense:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["software_product", "assignments"],
        )
        return item

    async def get(self, license_id: UUID) -> SoftwareLicense | None:
        stmt = (
            select(SoftwareLicense)
            .options(
                selectinload(SoftwareLicense.software_product),
                selectinload(SoftwareLicense.assignments).selectinload(
                    SoftwareLicenseAssignment.asset
                ),
            )
            .where(SoftwareLicense.id == license_id)
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        pagination: PaginationParams,
    ) -> tuple[Sequence[SoftwareLicense], int]:
        stmt: Select[tuple[SoftwareLicense]] = select(SoftwareLicense).options(
            selectinload(SoftwareLicense.software_product),
            selectinload(SoftwareLicense.assignments),
        )
        count_stmt = select(func.count()).select_from(SoftwareLicense)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            stmt = stmt.join(SoftwareLicense.software_product).where(
                SoftwareProduct.product_code.ilike(search_value)
                | SoftwareProduct.product_name.ilike(search_value)
                | SoftwareLicense.license_number.ilike(search_value)
            )
            count_stmt = count_stmt.join(SoftwareLicense.software_product).where(
                SoftwareProduct.product_code.ilike(search_value)
                | SoftwareProduct.product_name.ilike(search_value)
                | SoftwareLicense.license_number.ilike(search_value)
            )
        sort_column = getattr(SoftwareLicense, pagination.sort or "expiry_date")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(self, item: SoftwareLicense, **changes: object) -> SoftwareLicense:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["software_product", "assignments"],
        )
        return item


class SoftwareLicenseAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: SoftwareLicenseAssignment) -> SoftwareLicenseAssignment:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["asset"])
        return item

    async def get(self, assignment_id: UUID) -> SoftwareLicenseAssignment | None:
        stmt = (
            select(SoftwareLicenseAssignment)
            .options(selectinload(SoftwareLicenseAssignment.asset))
            .where(SoftwareLicenseAssignment.id == assignment_id)
        )
        return await self.session.scalar(stmt)

    async def list_active_by_license(
        self,
        license_id: UUID,
    ) -> Sequence[SoftwareLicenseAssignment]:
        stmt = (
            select(SoftwareLicenseAssignment)
            .options(selectinload(SoftwareLicenseAssignment.asset))
            .where(
                SoftwareLicenseAssignment.software_license_id == license_id,
                SoftwareLicenseAssignment.released_at.is_(None),
            )
            .order_by(SoftwareLicenseAssignment.assigned_at.asc())
        )
        items = await self.session.scalars(stmt)
        return items.all()
