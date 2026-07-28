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


class SoftwareProduct(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "software_products"

    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    publisher_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    publisher_name: Mapped[str | None] = mapped_column(String(150))
    product_type: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50))
    edition: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    publisher_partner = relationship("BusinessPartner")
    licenses: Mapped[list[SoftwareLicense]] = relationship(back_populates="software_product")


class SoftwareLicense(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "software_licenses"
    __table_args__ = (
        CheckConstraint("license_quantity >= 0", name="ck_software_licenses_quantity_non_negative"),
        CheckConstraint("used_quantity >= 0", name="ck_software_licenses_used_non_negative"),
        CheckConstraint(
            "used_quantity <= license_quantity",
            name="ck_software_licenses_used_not_exceed_quantity",
        ),
        CheckConstraint(
            "expiry_date IS NULL OR start_date IS NULL OR expiry_date >= start_date",
            name="ck_software_licenses_expiry_after_start",
        ),
    )

    software_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("software_products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    license_number: Mapped[str | None] = mapped_column(String(150))
    license_key_encrypted: Mapped[str | None] = mapped_column(Text)
    license_model: Mapped[str] = mapped_column(String(30), nullable=False)
    license_metric: Mapped[str] = mapped_column(String(30), nullable=False)
    license_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    used_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    activation_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    renewal_type: Mapped[str | None] = mapped_column(String(30))
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    renewal_notice_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    subscription_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    currency_code: Mapped[str | None] = mapped_column(String(3))
    supplier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    maintenance_contract_id: Mapped[UUID | None] = mapped_column(nullable=True)
    support_end_date: Mapped[date | None] = mapped_column(Date)
    update_entitlement_end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    software_product: Mapped[SoftwareProduct] = relationship(back_populates="licenses")
    supplier = relationship("BusinessPartner")
    assignments: Mapped[list[SoftwareLicenseAssignment]] = relationship(
        back_populates="software_license"
    )


class SoftwareLicenseAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "software_license_assignments"
    __table_args__ = (
        CheckConstraint(
            "(asset_id IS NOT NULL AND employee_id IS NULL) "
            "OR (asset_id IS NULL AND employee_id IS NOT NULL)",
            name="ck_software_license_assignments_target_choice",
        ),
        UniqueConstraint(
            "software_license_id",
            "asset_id",
            "employee_id",
            "assigned_at",
            name="uq_software_license_assignments_unique",
        ),
    )

    software_license_id: Mapped[UUID] = mapped_column(
        ForeignKey("software_licenses.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL")
    )
    employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    assignment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    software_license: Mapped[SoftwareLicense] = relationship(back_populates="assignments")
    asset = relationship("Asset")
