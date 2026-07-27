from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.schemas import AssetReference


class LeaseContractCreate(BaseModel):
    contract_number: str = Field(max_length=100)
    lessor_partner_id: UUID
    lessee_company_id: UUID | None = None
    lease_type: str = Field(max_length=30)
    accounting_treatment: str = Field(max_length=30)
    start_date: date
    end_date: date
    extension_option_end_date: date | None = None
    billing_frequency: str = Field(max_length=20)
    payment_amount: Decimal = Field(ge=0)
    currency_code: str = Field(min_length=3, max_length=3)
    deposit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    purchase_option_amount: Decimal | None = Field(default=None, ge=0)
    auto_renewal: bool = False
    notice_period_days: int | None = Field(default=None, ge=0)
    maintenance_included: bool = False
    insurance_included: bool = False
    tax_included: bool = False
    status: str = Field(max_length=20)


class LeaseContractAssetCreate(BaseModel):
    asset_id: UUID
    lease_start_date: date
    lease_end_date: date
    monthly_amount: Decimal | None = Field(default=None, ge=0)
    allocation_percentage: Decimal = Field(default=Decimal("100"), gt=0, le=100)
    return_condition: str | None = None
    returned_at: datetime | None = None


class LeasePaymentCreate(BaseModel):
    period_start: date
    period_end: date
    due_date: date
    principal_amount: Decimal = Field(default=Decimal("0"), ge=0)
    interest_amount: Decimal = Field(default=Decimal("0"), ge=0)
    service_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(ge=0)
    payment_status: str = Field(max_length=20)
    sap_ap_invoice_doc_entry: int | None = None
    sap_payment_doc_entry: int | None = None


class LeaseContractAssetRead(BaseModel):
    id: UUID
    lease_contract_id: UUID
    asset_id: UUID
    lease_start_date: date
    lease_end_date: date
    monthly_amount: Decimal | None
    allocation_percentage: Decimal
    return_condition: str | None
    returned_at: datetime | None
    asset: AssetReference

    @classmethod
    def from_model(cls, item: object) -> LeaseContractAssetRead:
        return cls(
            id=item.id,
            lease_contract_id=item.lease_contract_id,
            asset_id=item.asset_id,
            lease_start_date=item.lease_start_date,
            lease_end_date=item.lease_end_date,
            monthly_amount=item.monthly_amount,
            allocation_percentage=item.allocation_percentage,
            return_condition=item.return_condition,
            returned_at=item.returned_at,
            asset=AssetReference(
                id=item.asset.id,
                code=item.asset.asset_code,
                name=item.asset.asset_name,
            ),
        )


class LeasePaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lease_contract_id: UUID
    period_start: date
    period_end: date
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    service_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_status: str
    sap_ap_invoice_doc_entry: int | None
    sap_payment_doc_entry: int | None

    @classmethod
    def from_model(cls, item: object) -> LeasePaymentRead:
        return cls(
            id=item.id,
            lease_contract_id=item.lease_contract_id,
            period_start=item.period_start,
            period_end=item.period_end,
            due_date=item.due_date,
            principal_amount=item.principal_amount,
            interest_amount=item.interest_amount,
            service_amount=item.service_amount,
            tax_amount=item.tax_amount,
            total_amount=item.total_amount,
            payment_status=item.payment_status,
            sap_ap_invoice_doc_entry=item.sap_ap_invoice_doc_entry,
            sap_payment_doc_entry=item.sap_payment_doc_entry,
        )


class LeaseContractRead(BaseModel):
    id: UUID
    contract_number: str
    lessor_partner_id: UUID
    lessee_company_id: UUID | None
    lease_type: str
    accounting_treatment: str
    start_date: date
    end_date: date
    extension_option_end_date: date | None
    billing_frequency: str
    payment_amount: Decimal
    currency_code: str
    deposit_amount: Decimal
    purchase_option_amount: Decimal | None
    auto_renewal: bool
    notice_period_days: int | None
    maintenance_included: bool
    insurance_included: bool
    tax_included: bool
    status: str
    items: list[LeaseContractAssetRead] = []
    payments: list[LeasePaymentRead] = []

    @classmethod
    def from_model(cls, item: object) -> LeaseContractRead:
        return cls(
            id=item.id,
            contract_number=item.contract_number,
            lessor_partner_id=item.lessor_partner_id,
            lessee_company_id=item.lessee_company_id,
            lease_type=item.lease_type,
            accounting_treatment=item.accounting_treatment,
            start_date=item.start_date,
            end_date=item.end_date,
            extension_option_end_date=item.extension_option_end_date,
            billing_frequency=item.billing_frequency,
            payment_amount=item.payment_amount,
            currency_code=item.currency_code,
            deposit_amount=item.deposit_amount,
            purchase_option_amount=item.purchase_option_amount,
            auto_renewal=item.auto_renewal,
            notice_period_days=item.notice_period_days,
            maintenance_included=item.maintenance_included,
            insurance_included=item.insurance_included,
            tax_included=item.tax_included,
            status=item.status,
            items=[
                LeaseContractAssetRead.from_model(child)
                for child in getattr(item, "items", [])
            ],
            payments=[
                LeasePaymentRead.from_model(child)
                for child in getattr(item, "payments", [])
            ],
        )


class LeaseContractListItemRead(BaseModel):
    id: UUID
    contract_number: str
    lessor_partner_id: UUID
    lease_type: str
    start_date: date
    end_date: date
    billing_frequency: str
    payment_amount: Decimal
    currency_code: str
    status: str
    item_count: int

    @classmethod
    def from_model(cls, item: object) -> LeaseContractListItemRead:
        return cls(
            id=item.id,
            contract_number=item.contract_number,
            lessor_partner_id=item.lessor_partner_id,
            lease_type=item.lease_type,
            start_date=item.start_date,
            end_date=item.end_date,
            billing_frequency=item.billing_frequency,
            payment_amount=item.payment_amount,
            currency_code=item.currency_code,
            status=item.status,
            item_count=len(getattr(item, "items", [])),
        )
