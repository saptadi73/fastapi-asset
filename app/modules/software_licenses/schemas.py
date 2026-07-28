from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.schemas import AssetReference


class SoftwareProductCreate(BaseModel):
    product_code: str = Field(max_length=50)
    product_name: str = Field(max_length=150)
    publisher_partner_id: UUID | None = None
    publisher_name: str | None = Field(default=None, max_length=150)
    product_type: str = Field(max_length=30)
    version: str | None = Field(default=None, max_length=50)
    edition: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class SoftwareProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_code: str
    product_name: str
    publisher_partner_id: UUID | None
    publisher_name: str | None
    product_type: str
    version: str | None
    edition: str | None
    is_active: bool


class SoftwareLicenseCreate(BaseModel):
    software_product_id: UUID
    license_number: str | None = Field(default=None, max_length=150)
    license_key_encrypted: str | None = None
    license_model: str = Field(max_length=30)
    license_metric: str = Field(max_length=30)
    license_quantity: int = Field(ge=0)
    purchase_date: date | None = None
    activation_date: date | None = None
    start_date: date | None = None
    expiry_date: date | None = None
    renewal_type: str | None = Field(default=None, max_length=30)
    auto_renewal: bool = False
    renewal_notice_days: int = Field(default=30, ge=0)
    subscription_cost: Decimal | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    supplier_id: UUID | None = None
    maintenance_contract_id: UUID | None = None
    support_end_date: date | None = None
    update_entitlement_end_date: date | None = None
    status: str = Field(max_length=20)


class SoftwareLicenseAssignmentCreate(BaseModel):
    asset_id: UUID | None = None
    employee_id: UUID | None = None
    assignment_type: str = Field(max_length=30)
    assigned_at: datetime


class SoftwareLicenseAssignmentReleasePayload(BaseModel):
    released_at: datetime


class SoftwareLicenseAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    software_license_id: UUID
    asset_id: UUID | None
    employee_id: UUID | None
    assignment_type: str
    assigned_at: datetime
    released_at: datetime | None
    asset: AssetReference | None = None

    @classmethod
    def from_model(cls, item: object) -> SoftwareLicenseAssignmentRead:
        return cls(
            id=item.id,
            software_license_id=item.software_license_id,
            asset_id=item.asset_id,
            employee_id=item.employee_id,
            assignment_type=item.assignment_type,
            assigned_at=item.assigned_at,
            released_at=item.released_at,
            asset=(
                AssetReference(
                    id=item.asset.id,
                    code=item.asset.asset_code,
                    name=item.asset.asset_name,
                )
                if getattr(item, "asset", None) is not None
                else None
            ),
        )


class SoftwareLicenseRead(BaseModel):
    id: UUID
    software_product_id: UUID
    license_number: str | None
    license_model: str
    license_metric: str
    license_quantity: int
    used_quantity: int
    available_quantity: int
    purchase_date: date | None
    activation_date: date | None
    start_date: date | None
    expiry_date: date | None
    renewal_type: str | None
    auto_renewal: bool
    renewal_notice_days: int
    subscription_cost: Decimal | None
    currency_code: str | None
    supplier_id: UUID | None
    maintenance_contract_id: UUID | None
    support_end_date: date | None
    update_entitlement_end_date: date | None
    status: str
    capacity_full: bool
    expires_soon: bool
    software_product: SoftwareProductRead
    assignments: list[SoftwareLicenseAssignmentRead] = []

    @classmethod
    def from_model(cls, item: object, *, as_of: date) -> SoftwareLicenseRead:
        expiry_date = getattr(item, "expiry_date", None)
        renewal_notice_days = getattr(item, "renewal_notice_days", 30) or 30
        expires_soon = (
            expiry_date is not None
            and expiry_date >= as_of
            and (expiry_date - as_of).days <= renewal_notice_days
        )
        used_quantity = getattr(item, "used_quantity", 0)
        license_quantity = getattr(item, "license_quantity", 0)
        return cls(
            id=item.id,
            software_product_id=item.software_product_id,
            license_number=item.license_number,
            license_model=item.license_model,
            license_metric=item.license_metric,
            license_quantity=license_quantity,
            used_quantity=used_quantity,
            available_quantity=max(license_quantity - used_quantity, 0),
            purchase_date=item.purchase_date,
            activation_date=item.activation_date,
            start_date=item.start_date,
            expiry_date=item.expiry_date,
            renewal_type=item.renewal_type,
            auto_renewal=item.auto_renewal,
            renewal_notice_days=renewal_notice_days,
            subscription_cost=item.subscription_cost,
            currency_code=item.currency_code,
            supplier_id=item.supplier_id,
            maintenance_contract_id=item.maintenance_contract_id,
            support_end_date=item.support_end_date,
            update_entitlement_end_date=item.update_entitlement_end_date,
            status=item.status,
            capacity_full=used_quantity >= license_quantity,
            expires_soon=expires_soon,
            software_product=SoftwareProductRead.model_validate(item.software_product),
            assignments=[
                SoftwareLicenseAssignmentRead.from_model(child)
                for child in getattr(item, "assignments", [])
            ],
        )


class SoftwareLicenseListItemRead(BaseModel):
    id: UUID
    software_product_id: UUID
    product_code: str
    product_name: str
    license_model: str
    license_metric: str
    license_quantity: int
    used_quantity: int
    available_quantity: int
    expiry_date: date | None
    status: str
    capacity_full: bool
    expires_soon: bool

    @classmethod
    def from_model(cls, item: object, *, as_of: date) -> SoftwareLicenseListItemRead:
        expiry_date = getattr(item, "expiry_date", None)
        renewal_notice_days = getattr(item, "renewal_notice_days", 30) or 30
        expires_soon = (
            expiry_date is not None
            and expiry_date >= as_of
            and (expiry_date - as_of).days <= renewal_notice_days
        )
        used_quantity = getattr(item, "used_quantity", 0)
        license_quantity = getattr(item, "license_quantity", 0)
        return cls(
            id=item.id,
            software_product_id=item.software_product_id,
            product_code=item.software_product.product_code,
            product_name=item.software_product.product_name,
            license_model=item.license_model,
            license_metric=item.license_metric,
            license_quantity=license_quantity,
            used_quantity=used_quantity,
            available_quantity=max(license_quantity - used_quantity, 0),
            expiry_date=item.expiry_date,
            status=item.status,
            capacity_full=used_quantity >= license_quantity,
            expires_soon=expires_soon,
        )
