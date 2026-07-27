from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.types import UUIDPrimaryKeyMixin


class AssetLeaseContract(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_lease_contracts"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_asset_lease_contracts_period"),
    )

    contract_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    lessor_partner_id: Mapped[UUID] = mapped_column(
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    lessee_company_id: Mapped[UUID | None] = mapped_column(nullable=True)
    lease_type: Mapped[str] = mapped_column(String(30), nullable=False)
    accounting_treatment: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    extension_option_end_date: Mapped[date | None] = mapped_column(Date)
    billing_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    purchase_option_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notice_period_days: Mapped[int | None] = mapped_column(Integer)
    maintenance_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    insurance_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tax_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    lessor_partner = relationship("BusinessPartner")
    items: Mapped[list[AssetLeaseItem]] = relationship(back_populates="lease_contract")
    payments: Mapped[list[AssetLeasePayment]] = relationship(back_populates="lease_contract")


class AssetLeaseItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_lease_items"
    __table_args__ = (
        UniqueConstraint(
            "lease_contract_id",
            "asset_id",
            "lease_start_date",
            name="uq_asset_lease_items_contract_asset_start",
        ),
        CheckConstraint(
            "allocation_percentage > 0 AND allocation_percentage <= 100",
            name="ck_asset_lease_items_allocation_range",
        ),
        CheckConstraint(
            "lease_end_date >= lease_start_date",
            name="ck_asset_lease_items_period",
        ),
    )

    lease_contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_lease_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    lease_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    lease_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    allocation_percentage: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=100,
        nullable=False,
    )
    return_condition: Mapped[str | None] = mapped_column(Text)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lease_contract: Mapped[AssetLeaseContract] = relationship(back_populates="items")
    asset = relationship("Asset")


class AssetLeasePayment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_lease_payments"
    __table_args__ = (
        UniqueConstraint(
            "lease_contract_id",
            "period_start",
            "period_end",
            name="uq_asset_lease_payments_contract_period",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_asset_lease_payments_period",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_asset_lease_payments_total_non_negative",
        ),
    )

    lease_contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_lease_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    service_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    sap_ap_invoice_doc_entry: Mapped[int | None] = mapped_column(Integer)
    sap_payment_doc_entry: Mapped[int | None] = mapped_column(Integer)

    lease_contract: Mapped[AssetLeaseContract] = relationship(back_populates="payments")
