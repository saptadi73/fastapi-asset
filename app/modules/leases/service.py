from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.assets.exceptions import AssetNotFoundError
from app.modules.assets.repository import AssetRepository
from app.modules.leases.models import AssetLeaseContract, AssetLeaseItem, AssetLeasePayment
from app.modules.leases.repository import (
    LeaseContractRepository,
    LeaseItemRepository,
    LeasePaymentRepository,
)
from app.modules.leases.schemas import (
    LeaseContractAssetCreate,
    LeaseContractCreate,
    LeasePaymentCreate,
)
from app.modules.partners.exceptions import BusinessPartnerNotFoundError
from app.modules.partners.repository import BusinessPartnerRepository
from app.shared.pagination import PaginationParams


class LeaseContractNotFoundError(AppError):
    def __init__(self, contract_id: str) -> None:
        super().__init__(
            code="LEASE_CONTRACT_NOT_FOUND",
            message=f"Lease contract {contract_id} tidak ditemukan.",
            status_code=404,
        )


class LeaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.contracts = LeaseContractRepository(session)
        self.items = LeaseItemRepository(session)
        self.payments = LeasePaymentRepository(session)
        self.assets = AssetRepository(session)
        self.partners = BusinessPartnerRepository(session)

    async def create_contract(self, payload: LeaseContractCreate) -> AssetLeaseContract:
        self._validate_contract_dates(
            payload.start_date,
            payload.end_date,
            payload.extension_option_end_date,
        )
        await self._get_partner_or_raise(payload.lessor_partner_id)
        item = AssetLeaseContract(**payload.model_dump())
        try:
            await self.contracts.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="LEASE_CONTRACT_CONFLICT",
                message="Lease contract number sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_contract(item.id)

    async def list_contracts(
        self,
        pagination: PaginationParams,
    ) -> tuple[list[AssetLeaseContract], int]:
        items, total_items = await self.contracts.list(pagination)
        return list(items), total_items

    async def get_contract(self, contract_id: UUID) -> AssetLeaseContract:
        item = await self.contracts.get(contract_id)
        if item is None:
            raise LeaseContractNotFoundError(str(contract_id))
        return item

    async def add_contract_asset(
        self,
        contract_id: UUID,
        payload: LeaseContractAssetCreate,
    ) -> AssetLeaseContract:
        contract = await self.get_contract(contract_id)
        await self._get_asset_or_raise(payload.asset_id)
        self._validate_item_period(contract.start_date, contract.end_date, payload)
        if payload.returned_at is None:
            await self._validate_asset_overlap(
                payload.asset_id,
                payload.lease_start_date,
                payload.lease_end_date,
            )
        item = AssetLeaseItem(
            lease_contract_id=contract.id,
            asset_id=payload.asset_id,
            lease_start_date=payload.lease_start_date,
            lease_end_date=payload.lease_end_date,
            monthly_amount=payload.monthly_amount,
            allocation_percentage=payload.allocation_percentage,
            return_condition=payload.return_condition,
            returned_at=payload.returned_at,
        )
        try:
            await self.items.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="LEASE_CONTRACT_ASSET_CONFLICT",
                message="Lease asset item menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_contract(contract_id)

    async def list_contract_assets(self, contract_id: UUID) -> list[AssetLeaseItem]:
        await self.get_contract(contract_id)
        return list(await self.items.list_by_contract(contract_id))

    async def add_payment(
        self,
        contract_id: UUID,
        payload: LeasePaymentCreate,
    ) -> AssetLeaseContract:
        contract = await self.get_contract(contract_id)
        self._validate_payment_period(payload.period_start, payload.period_end, payload.due_date)
        self._validate_payment_within_contract(
            contract.start_date,
            contract.end_date,
            payload.period_start,
            payload.period_end,
        )
        payment = AssetLeasePayment(
            lease_contract_id=contract.id,
            period_start=payload.period_start,
            period_end=payload.period_end,
            due_date=payload.due_date,
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount,
            service_amount=payload.service_amount,
            tax_amount=payload.tax_amount,
            total_amount=payload.total_amount,
            payment_status=payload.payment_status,
            sap_ap_invoice_doc_entry=payload.sap_ap_invoice_doc_entry,
            sap_payment_doc_entry=payload.sap_payment_doc_entry,
        )
        try:
            await self.payments.create(payment)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="LEASE_PAYMENT_CONFLICT",
                message="Lease payment untuk periode yang sama sudah ada.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_contract(contract_id)

    async def list_payments(self, contract_id: UUID) -> list[AssetLeasePayment]:
        await self.get_contract(contract_id)
        return list(await self.payments.list_by_contract(contract_id))

    def _validate_contract_dates(
        self,
        start_date: date,
        end_date: date,
        extension_option_end_date: date | None,
    ) -> None:
        if end_date < start_date:
            raise AppError(
                code="LEASE_CONTRACT_PERIOD_INVALID",
                message="end_date tidak boleh lebih kecil dari start_date.",
                status_code=422,
            )
        if extension_option_end_date is not None and extension_option_end_date < end_date:
            raise AppError(
                code="LEASE_CONTRACT_EXTENSION_INVALID",
                message="extension_option_end_date tidak boleh lebih kecil dari end_date.",
                status_code=422,
            )

    def _validate_item_period(
        self,
        contract_start_date: date,
        contract_end_date: date,
        payload: LeaseContractAssetCreate,
    ) -> None:
        if payload.lease_end_date < payload.lease_start_date:
            raise AppError(
                code="LEASE_ITEM_PERIOD_INVALID",
                message="lease_end_date tidak boleh lebih kecil dari lease_start_date.",
                status_code=422,
            )
        if (
            payload.lease_start_date < contract_start_date
            or payload.lease_end_date > contract_end_date
        ):
            raise AppError(
                code="LEASE_ITEM_OUTSIDE_CONTRACT_PERIOD",
                message="Periode lease item harus berada dalam periode lease contract.",
                status_code=422,
            )

    async def _validate_asset_overlap(
        self,
        asset_id: UUID,
        lease_start_date: date,
        lease_end_date: date,
    ) -> None:
        overlaps = await self.items.list_active_overlaps(
            asset_id,
            lease_start_date=lease_start_date,
            lease_end_date=lease_end_date,
        )
        if overlaps:
            raise AppError(
                code="LEASE_ACTIVE_OVERLAP_NOT_ALLOWED",
                message="Aset tidak boleh memiliki active lease item yang overlap.",
                status_code=409,
            )

    def _validate_payment_period(
        self,
        period_start: date,
        period_end: date,
        due_date: date,
    ) -> None:
        if period_end < period_start:
            raise AppError(
                code="LEASE_PAYMENT_PERIOD_INVALID",
                message="period_end tidak boleh lebih kecil dari period_start.",
                status_code=422,
            )
        if due_date < period_start:
            raise AppError(
                code="LEASE_PAYMENT_DUE_DATE_INVALID",
                message="due_date tidak boleh lebih kecil dari period_start.",
                status_code=422,
            )

    def _validate_payment_within_contract(
        self,
        contract_start_date: date,
        contract_end_date: date,
        period_start: date,
        period_end: date,
    ) -> None:
        if period_start < contract_start_date or period_end > contract_end_date:
            raise AppError(
                code="LEASE_PAYMENT_OUTSIDE_CONTRACT_PERIOD",
                message="Periode payment harus berada dalam periode lease contract.",
                status_code=422,
            )

    async def _get_asset_or_raise(self, asset_id: UUID):
        asset = await self.assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))
        return asset

    async def _get_partner_or_raise(self, partner_id: UUID):
        partner = await self.partners.get(partner_id)
        if partner is None:
            raise BusinessPartnerNotFoundError(str(partner_id))
        return partner
