from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.types import TimestampMixin, UUIDPrimaryKeyMixin


class BusinessPartner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_partners"

    partner_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    partner_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_number: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    sap_card_code: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list[BusinessPartnerRole]] = relationship(
        back_populates="business_partner",
        cascade="all, delete-orphan",
    )


class BusinessPartnerRole(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "business_partner_roles"
    __table_args__ = (
        UniqueConstraint(
            "business_partner_id",
            "role_type",
            "valid_from",
            name="uq_business_partner_role_valid_from",
        ),
    )

    business_partner_id: Mapped[UUID] = mapped_column(
        ForeignKey("business_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_type: Mapped[str] = mapped_column(String(30), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    business_partner: Mapped[BusinessPartner] = relationship(back_populates="roles")
