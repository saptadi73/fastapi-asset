from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.assets.exceptions import AssetNotFoundError
from app.modules.assets.repository import AssetRepository
from app.modules.partners.exceptions import BusinessPartnerNotFoundError
from app.modules.partners.repository import BusinessPartnerRepository
from app.modules.software_licenses.models import (
    SoftwareLicense,
    SoftwareLicenseAssignment,
    SoftwareProduct,
)
from app.modules.software_licenses.repository import (
    SoftwareLicenseAssignmentRepository,
    SoftwareLicenseRepository,
    SoftwareProductRepository,
)
from app.modules.software_licenses.schemas import (
    SoftwareLicenseAssignmentCreate,
    SoftwareLicenseAssignmentReleasePayload,
    SoftwareLicenseCreate,
    SoftwareProductCreate,
)
from app.shared.pagination import PaginationParams


class SoftwareProductNotFoundError(AppError):
    def __init__(self, product_id: str) -> None:
        super().__init__(
            code="SOFTWARE_PRODUCT_NOT_FOUND",
            message=f"Software product {product_id} tidak ditemukan.",
            status_code=404,
        )


class SoftwareLicenseNotFoundError(AppError):
    def __init__(self, license_id: str) -> None:
        super().__init__(
            code="SOFTWARE_LICENSE_NOT_FOUND",
            message=f"Software license {license_id} tidak ditemukan.",
            status_code=404,
        )


class SoftwareLicenseAssignmentNotFoundError(AppError):
    def __init__(self, assignment_id: str) -> None:
        super().__init__(
            code="SOFTWARE_LICENSE_ASSIGNMENT_NOT_FOUND",
            message=f"Software license assignment {assignment_id} tidak ditemukan.",
            status_code=404,
        )


class SoftwareLicenseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = SoftwareProductRepository(session)
        self.licenses = SoftwareLicenseRepository(session)
        self.assignments = SoftwareLicenseAssignmentRepository(session)
        self.assets = AssetRepository(session)
        self.partners = BusinessPartnerRepository(session)

    async def create_product(self, payload: SoftwareProductCreate) -> SoftwareProduct:
        if payload.publisher_partner_id is not None:
            await self._get_partner_or_raise(payload.publisher_partner_id)
        item = SoftwareProduct(**payload.model_dump())
        try:
            await self.products.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="SOFTWARE_PRODUCT_CONFLICT",
                message="Product code software sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return item

    async def list_products(self) -> list[SoftwareProduct]:
        return list(await self.products.list())

    async def create_license(self, payload: SoftwareLicenseCreate) -> SoftwareLicense:
        await self._get_product_or_raise(payload.software_product_id)
        if payload.supplier_id is not None:
            await self._get_partner_or_raise(payload.supplier_id)
        self._validate_license_dates(payload.start_date, payload.expiry_date)
        item = SoftwareLicense(
            **payload.model_dump(),
            used_quantity=0,
        )
        try:
            await self.licenses.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="SOFTWARE_LICENSE_CONFLICT",
                message="Software license menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_license(item.id)

    async def list_licenses(
        self,
        pagination: PaginationParams,
    ) -> tuple[list[SoftwareLicense], int]:
        items, total_items = await self.licenses.list(pagination)
        return list(items), total_items

    async def get_license(self, license_id: UUID) -> SoftwareLicense:
        item = await self.licenses.get(license_id)
        if item is None:
            raise SoftwareLicenseNotFoundError(str(license_id))
        return item

    async def assign_license(
        self,
        license_id: UUID,
        payload: SoftwareLicenseAssignmentCreate,
    ) -> SoftwareLicense:
        item = await self.get_license(license_id)
        self._validate_assignment_target(payload.asset_id, payload.employee_id)
        if payload.asset_id is not None:
            await self._get_asset_or_raise(payload.asset_id)
        self._validate_license_assignable(item, payload.assigned_at.date())
        active_assignments = await self.assignments.list_active_by_license(item.id)
        if len(active_assignments) >= item.license_quantity:
            raise AppError(
                code="SOFTWARE_LICENSE_CAPACITY_FULL",
                message="Kapasitas software license sudah penuh.",
                status_code=409,
            )
        assignment = SoftwareLicenseAssignment(
            software_license_id=item.id,
            asset_id=payload.asset_id,
            employee_id=payload.employee_id,
            assignment_type=payload.assignment_type,
            assigned_at=payload.assigned_at,
        )
        try:
            await self.assignments.create(assignment)
            await self._sync_used_quantity(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="SOFTWARE_LICENSE_ASSIGNMENT_CONFLICT",
                message="Software license assignment menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_license(license_id)

    async def release_assignment(
        self,
        assignment_id: UUID,
        payload: SoftwareLicenseAssignmentReleasePayload,
    ) -> SoftwareLicenseAssignment:
        assignment = await self.assignments.get(assignment_id)
        if assignment is None:
            raise SoftwareLicenseAssignmentNotFoundError(str(assignment_id))
        if assignment.released_at is not None:
            raise AppError(
                code="SOFTWARE_LICENSE_ASSIGNMENT_ALREADY_RELEASED",
                message="Software license assignment sudah direlease.",
                status_code=409,
            )
        if payload.released_at < assignment.assigned_at:
            raise AppError(
                code="SOFTWARE_LICENSE_ASSIGNMENT_RELEASE_TIME_INVALID",
                message="released_at tidak boleh lebih kecil dari assigned_at.",
                status_code=422,
            )
        license_item = await self.get_license(assignment.software_license_id)
        try:
            assignment.released_at = payload.released_at
            await self._sync_used_quantity(license_item)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        refreshed = await self.assignments.get(assignment_id)
        if refreshed is None:
            raise SoftwareLicenseAssignmentNotFoundError(str(assignment_id))
        return refreshed

    def _validate_license_dates(
        self,
        start_date: date | None,
        expiry_date: date | None,
    ) -> None:
        if start_date is not None and expiry_date is not None and expiry_date < start_date:
            raise AppError(
                code="SOFTWARE_LICENSE_PERIOD_INVALID",
                message="expiry_date tidak boleh lebih kecil dari start_date.",
                status_code=422,
            )

    def _validate_assignment_target(
        self,
        asset_id: UUID | None,
        employee_id: UUID | None,
    ) -> None:
        if (asset_id is None and employee_id is None) or (
            asset_id is not None and employee_id is not None
        ):
            raise AppError(
                code="SOFTWARE_LICENSE_ASSIGNMENT_TARGET_INVALID",
                message="Assignment harus memilih tepat satu target: asset atau employee.",
                status_code=422,
            )

    def _validate_license_assignable(
        self,
        item: SoftwareLicense,
        as_of: date,
    ) -> None:
        if item.status not in {"ACTIVE", "IN_USE"}:
            raise AppError(
                code="SOFTWARE_LICENSE_STATUS_INVALID",
                message="Software license belum berada pada status yang mengizinkan assignment.",
                status_code=409,
            )
        if item.start_date is not None and as_of < item.start_date:
            raise AppError(
                code="SOFTWARE_LICENSE_NOT_EFFECTIVE_YET",
                message="Software license belum efektif pada tanggal assignment.",
                status_code=422,
            )
        if item.expiry_date is not None and as_of > item.expiry_date:
            raise AppError(
                code="SOFTWARE_LICENSE_EXPIRED",
                message="Software license sudah expired.",
                status_code=422,
            )

    async def _sync_used_quantity(self, item: SoftwareLicense) -> None:
        active_assignments = await self.assignments.list_active_by_license(item.id)
        await self.licenses.update(item, used_quantity=len(active_assignments))

    async def _get_product_or_raise(self, product_id: UUID) -> SoftwareProduct:
        item = await self.products.get(product_id)
        if item is None:
            raise SoftwareProductNotFoundError(str(product_id))
        return item

    async def _get_partner_or_raise(self, partner_id: UUID):
        partner = await self.partners.get(partner_id)
        if partner is None:
            raise BusinessPartnerNotFoundError(str(partner_id))
        return partner

    async def _get_asset_or_raise(self, asset_id: UUID):
        asset = await self.assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))
        return asset
