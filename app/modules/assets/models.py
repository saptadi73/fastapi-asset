from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
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
from app.shared.types import TimestampMixin, UUIDPrimaryKeyMixin


class AssetCategory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_categories"

    category_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category_name: Mapped[str] = mapped_column(String(150), nullable=False)
    parent_category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_categories.id", ondelete="RESTRICT")
    )
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent_category: Mapped[AssetCategory | None] = relationship(
        remote_side="AssetCategory.id"
    )


class AssetClass(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_classes"

    class_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    class_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sap_asset_class_code: Mapped[str | None] = mapped_column(String(50))
    default_useful_life_months: Mapped[int | None] = mapped_column(Integer)
    is_depreciable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AssetLocation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_locations"

    location_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    location_name: Mapped[str] = mapped_column(String(150), nullable=False)
    location_type: Mapped[str] = mapped_column(String(30), nullable=False)
    parent_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT")
    )
    company_id: Mapped[UUID | None] = mapped_column(nullable=True)
    branch_id: Mapped[UUID | None] = mapped_column(nullable=True)
    warehouse_code: Mapped[str | None] = mapped_column(String(50))
    bin_location_code: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent_location: Mapped[AssetLocation | None] = relationship(
        remote_side="AssetLocation.id"
    )


class AssetAttributeDefinition(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_attribute_definitions"
    __table_args__ = (
        UniqueConstraint(
            "asset_category_id",
            "attribute_code",
            name="uq_asset_attribute_definitions_category_code",
        ),
    )

    asset_category_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attribute_code: Mapped[str] = mapped_column(String(50), nullable=False)
    attribute_name: Mapped[str] = mapped_column(String(150), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(30))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_rule: Mapped[dict | None] = mapped_column(JSON)

    asset_category: Mapped[AssetCategory] = relationship()


class AssetAttributeValue(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_attribute_values"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "attribute_definition_id",
            name="uq_asset_attribute_values_asset_definition",
        ),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attribute_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_attribute_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    value_date: Mapped[date | None] = mapped_column(Date)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_json: Mapped[dict | None] = mapped_column(JSON)

    asset: Mapped[Asset] = relationship(back_populates="attribute_values")
    attribute_definition: Mapped[AssetAttributeDefinition] = relationship()


class AssetOwnership(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_ownerships"
    __table_args__ = (
        CheckConstraint(
            "ownership_percentage > 0 AND ownership_percentage <= 100",
            name="ck_asset_ownerships_percentage_range",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_asset_ownerships_effective_period",
        ),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_type: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    owner_company_id: Mapped[UUID | None] = mapped_column(nullable=True)
    ownership_percentage: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_reference: Mapped[str | None] = mapped_column(String(150))
    notes: Mapped[str | None] = mapped_column(Text)

    asset: Mapped[Asset] = relationship(back_populates="ownerships")


class AssetTransfer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_transfers"

    transfer_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    transfer_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    transfer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    movement_purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expected_return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    from_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="SET NULL")
    )
    to_location_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_department_id: Mapped[UUID | None] = mapped_column(nullable=True)
    to_department_id: Mapped[UUID | None] = mapped_column(nullable=True)
    requested_by: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatched_by: Mapped[UUID | None] = mapped_column(nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_by: Mapped[UUID | None] = mapped_column(nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)

    from_location: Mapped[AssetLocation | None] = relationship(foreign_keys=[from_location_id])
    to_location: Mapped[AssetLocation] = relationship(foreign_keys=[to_location_id])
    items: Mapped[list[AssetTransferItem]] = relationship(back_populates="transfer")


class AssetTransferItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_transfer_items"
    __table_args__ = (
        UniqueConstraint(
            "asset_transfer_id",
            "asset_id",
            name="uq_asset_transfer_items_transfer_asset",
        ),
    )

    asset_transfer_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_transfers.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_custodian_id: Mapped[UUID | None] = mapped_column(nullable=True)
    new_custodian_id: Mapped[UUID | None] = mapped_column(nullable=True)
    handover_condition: Mapped[str] = mapped_column(String(30), nullable=False)
    dispatch_scan_event_id: Mapped[UUID | None] = mapped_column(nullable=True)
    receipt_scan_event_id: Mapped[UUID | None] = mapped_column(nullable=True)
    item_status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    transfer: Mapped[AssetTransfer] = relationship(back_populates="items")
    asset: Mapped[Asset] = relationship()


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint(
            "parent_asset_id IS NULL OR parent_asset_id <> id",
            name="ck_assets_no_self_parent",
        ),
        CheckConstraint(
            "manufacture_year IS NULL OR manufacture_year BETWEEN 1900 AND 2200",
            name="ck_assets_manufacture_year",
        ),
        CheckConstraint(
            (
                "retirement_date IS NULL OR in_service_date IS NULL "
                "OR retirement_date >= in_service_date"
            ),
            name="ck_assets_retirement_after_service",
        ),
    )

    asset_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    asset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    asset_category_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    asset_class_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_classes.id", ondelete="SET NULL")
    )
    parent_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT")
    )

    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    asset_status: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_status: Mapped[str] = mapped_column(String(30), nullable=False)
    criticality_level: Mapped[str | None] = mapped_column(String(20))

    serial_number: Mapped[str | None] = mapped_column(String(150))
    manufacturer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    brand: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    manufacture_year: Mapped[int | None] = mapped_column(Integer)

    company_id: Mapped[UUID | None] = mapped_column(nullable=True)
    branch_id: Mapped[UUID | None] = mapped_column(nullable=True)
    current_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="SET NULL")
    )
    current_primary_custodian_id: Mapped[UUID | None] = mapped_column(nullable=True)

    barcode: Mapped[str | None] = mapped_column(String(100))
    qr_code: Mapped[str | None] = mapped_column(String(200))
    tag_number: Mapped[str | None] = mapped_column(String(100))
    tracking_status: Mapped[str] = mapped_column(String(20), default="TRACKED", nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_verified_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="SET NULL")
    )

    in_service_date: Mapped[date | None] = mapped_column(Date)
    retirement_date: Mapped[date | None] = mapped_column(Date)
    expected_replacement_date: Mapped[date | None] = mapped_column(Date)
    support_end_date: Mapped[date | None] = mapped_column(Date)
    vendor_end_of_sale_date: Mapped[date | None] = mapped_column(Date)
    vendor_end_of_support_date: Mapped[date | None] = mapped_column(Date)
    replacement_strategy: Mapped[str | None] = mapped_column(String(30))
    replacement_priority: Mapped[str | None] = mapped_column(String(20))
    estimated_replacement_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    replacement_budget_year: Mapped[int | None] = mapped_column(Integer)
    next_review_date: Mapped[date | None] = mapped_column(Date)

    sap_asset_code: Mapped[str | None] = mapped_column(String(50))
    sap_item_code: Mapped[str | None] = mapped_column(String(50))

    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)

    asset_category: Mapped[AssetCategory] = relationship()
    asset_class: Mapped[AssetClass | None] = relationship()
    parent_asset: Mapped[Asset | None] = relationship(remote_side="Asset.id")
    current_location: Mapped[AssetLocation | None] = relationship(
        foreign_keys=[current_location_id]
    )
    last_verified_location: Mapped[AssetLocation | None] = relationship(
        foreign_keys=[last_verified_location_id]
    )
    attribute_values: Mapped[list[AssetAttributeValue]] = relationship(
        back_populates="asset"
    )
    ownerships: Mapped[list[AssetOwnership]] = relationship(back_populates="asset")
    lifecycle_reviews: Mapped[list[AssetLifecycleReview]] = relationship(
        back_populates="asset"
    )
    retirements: Mapped[list[AssetRetirement]] = relationship(back_populates="asset")
    component_histories: Mapped[list[AssetComponentHistory]] = relationship(
        back_populates="asset",
        foreign_keys="AssetComponentHistory.asset_id",
    )


class AssetLocationHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_location_histories"

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="SET NULL")
    )
    to_location_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    transfer_id: Mapped[UUID | None] = mapped_column(nullable=True)
    reason: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[UUID | None] = mapped_column(nullable=True)

    asset: Mapped[Asset] = relationship()
    from_location: Mapped[AssetLocation | None] = relationship(
        foreign_keys=[from_location_id]
    )
    to_location: Mapped[AssetLocation] = relationship(foreign_keys=[to_location_id])


class AssetAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_assignments"
    __table_args__ = (
        CheckConstraint(
            "returned_at IS NULL OR returned_at >= assigned_at",
            name="ck_asset_assignments_returned_after_assigned",
        ),
        UniqueConstraint("id", "asset_id", name="uq_asset_assignments_id_asset"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assignment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    department_id: Mapped[UUID | None] = mapped_column(nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_return_date: Mapped[date | None] = mapped_column(Date)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    handover_document_id: Mapped[UUID | None] = mapped_column(nullable=True)
    accepted_by_employee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_by_employee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assignment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    asset: Mapped[Asset] = relationship()


class AssetStatusHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_status_histories"

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    previous_condition: Mapped[str | None] = mapped_column(String(30))
    new_condition: Mapped[str | None] = mapped_column(String(30))
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[UUID | None] = mapped_column(nullable=True)
    changed_by: Mapped[UUID | None] = mapped_column(nullable=True)

    asset: Mapped[Asset] = relationship()


class AssetLifecycleReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_lifecycle_reviews"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "review_date",
            name="uq_asset_lifecycle_reviews_asset_date",
        ),
        CheckConstraint(
            "condition_score >= 0 AND condition_score <= 100",
            name="ck_asset_lifecycle_reviews_condition_score",
        ),
        CheckConstraint(
            "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)",
            name="ck_asset_lifecycle_reviews_risk_score",
        ),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    condition_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    remaining_life_months: Mapped[int | None] = mapped_column(Integer)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    replacement_recommendation: Mapped[str] = mapped_column(String(30), nullable=False)
    estimated_replacement_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="lifecycle_reviews")


class AssetRetirement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_retirements"
    __table_args__ = (
        UniqueConstraint("retirement_number", name="uq_asset_retirements_number"),
        CheckConstraint(
            "effective_date IS NULL OR effective_date >= request_date",
            name="ck_asset_retirements_effective_after_request",
        ),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    retirement_number: Mapped[str] = mapped_column(String(50), nullable=False)
    retirement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    request_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    proceeds_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        nullable=False,
        default=Decimal("0"),
    )
    buyer_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[UUID | None] = mapped_column(nullable=True)
    sap_retirement_doc_entry: Mapped[int | None] = mapped_column(Integer)
    sap_trans_id: Mapped[int | None] = mapped_column(Integer)

    asset: Mapped[Asset] = relationship(back_populates="retirements")


class AssetComponentHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_component_histories"
    __table_args__ = (
        CheckConstraint(
            "("
            "(action_type = 'INSTALL' AND installed_component_asset_id IS NOT NULL "
            "AND removed_component_asset_id IS NULL)"
            " OR "
            "(action_type = 'REMOVE' AND installed_component_asset_id IS NULL "
            "AND removed_component_asset_id IS NOT NULL)"
            " OR "
            "(action_type = 'REPLACE' AND installed_component_asset_id IS NOT NULL "
            "AND removed_component_asset_id IS NOT NULL)"
            ")",
            name="ck_asset_component_histories_action_targets",
        ),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    removed_component_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL")
    )
    installed_component_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL")
    )
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    work_order_id: Mapped[UUID | None] = mapped_column(nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[UUID | None] = mapped_column(nullable=True)
    changed_by: Mapped[UUID | None] = mapped_column(nullable=True)

    asset: Mapped[Asset] = relationship(
        back_populates="component_histories",
        foreign_keys=[asset_id],
    )
    removed_component_asset: Mapped[Asset | None] = relationship(
        foreign_keys=[removed_component_asset_id]
    )
    installed_component_asset: Mapped[Asset | None] = relationship(
        foreign_keys=[installed_component_asset_id]
    )
