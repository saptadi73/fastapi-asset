from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.types import TimestampMixin, UUIDPrimaryKeyMixin


class MaintenancePriority(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_priorities"

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    severity_level: Mapped[int] = mapped_column(Integer, nullable=False)
    default_response_minutes: Mapped[int | None] = mapped_column(Integer)
    default_resolution_minutes: Mapped[int | None] = mapped_column(Integer)
    escalation_after_minutes: Mapped[int | None] = mapped_column(Integer)
    color_code: Mapped[str | None] = mapped_column(String(20))
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MaintenanceContract(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_contracts"

    contract_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    contract_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vendor_partner_id: Mapped[UUID] = mapped_column(
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    contract_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    response_time_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    resolution_time_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    preventive_maintenance_included: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    corrective_maintenance_included: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    spare_parts_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    labor_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onsite_support_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remote_support_included: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    currency_code: Mapped[str | None] = mapped_column(String(3))
    billing_frequency: Mapped[str | None] = mapped_column(String(20))
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notice_period_days: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    sap_purchase_contract_reference: Mapped[str | None] = mapped_column(String(100))

    vendor_partner = relationship("BusinessPartner")
    coverages: Mapped[list[MaintenanceContractAsset]] = relationship(
        back_populates="contract"
    )


class MaintenanceContractAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_contract_assets"
    __table_args__ = (
        UniqueConstraint(
            "maintenance_contract_id",
            "asset_id",
            "coverage_start_date",
            name="uq_maintenance_contract_assets_contract_asset_start",
        ),
    )

    maintenance_contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    coverage_start_date: Mapped[date] = mapped_column(nullable=False)
    coverage_end_date: Mapped[date] = mapped_column(nullable=False)
    coverage_level: Mapped[str] = mapped_column(String(30), nullable=False)
    annual_allocation_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    specific_exclusions: Mapped[str | None] = mapped_column(Text)

    contract: Mapped[MaintenanceContract] = relationship(back_populates="coverages")
    asset = relationship("Asset")


class AssetWarranty(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_warranties"

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    warranty_provider_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    warranty_type: Mapped[str] = mapped_column(String(30), nullable=False)
    warranty_number: Mapped[str | None] = mapped_column(String(100))
    coverage_start_date: Mapped[date] = mapped_column(nullable=False)
    coverage_end_date: Mapped[date] = mapped_column(nullable=False)
    claim_deadline_date: Mapped[date | None] = mapped_column(nullable=True)
    coverage_scope: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    asset = relationship("Asset")
    warranty_provider_partner = relationship("BusinessPartner")
    claims: Mapped[list[AssetWarrantyClaim]] = relationship(back_populates="warranty")


class AssetWarrantyClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_warranty_claims"

    warranty_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_warranties.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    claim_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    claim_date: Mapped[date] = mapped_column(nullable=False)
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    claim_status: Mapped[str] = mapped_column(String(30), nullable=False)
    resolution_description: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replacement_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL")
    )
    cost_covered: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    cost_not_covered: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))

    warranty: Mapped[AssetWarranty] = relationship(back_populates="claims")
    asset = relationship("Asset", foreign_keys=[asset_id])
    replacement_asset = relationship("Asset", foreign_keys=[replacement_asset_id])


class MaintenanceRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_requests"

    request_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    company_id: Mapped[UUID] = mapped_column(nullable=False)
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="SET NULL")
    )
    request_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    requested_by_employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    reported_by_name: Mapped[str | None] = mapped_column(String(150))
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    priority_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_priorities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    asset_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="SET NULL")
    )
    operating_condition: Mapped[str | None] = mapped_column(Text)
    is_asset_stopped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    downtime_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    safety_impact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    environmental_impact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    production_impact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintenance_contract_id: Mapped[UUID | None] = mapped_column(nullable=True)
    warranty_id: Mapped[UUID | None] = mapped_column(nullable=True)
    requested_vendor_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    triaged_by_employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    required_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    required_resolution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    asset = relationship("Asset")
    parent_request: Mapped[MaintenanceRequest | None] = relationship(
        remote_side="MaintenanceRequest.id"
    )
    priority: Mapped[MaintenancePriority] = relationship()
    asset_location = relationship("AssetLocation")
    requested_vendor_partner = relationship("BusinessPartner")
    work_orders: Mapped[list[MaintenanceRequestWorkOrder]] = relationship(back_populates="request")
    sla_snapshots: Mapped[list[MaintenanceSlaSnapshot]] = relationship(
        back_populates="maintenance_request"
    )


class MaintenanceWorkOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_work_orders"

    work_order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    company_id: Mapped[UUID] = mapped_column(nullable=False)
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    maintenance_type: Mapped[str] = mapped_column(String(30), nullable=False)
    priority_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_priorities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    scope_of_work: Mapped[str] = mapped_column(Text, nullable=False)
    maintenance_plan_id: Mapped[UUID | None] = mapped_column(nullable=True)
    maintenance_team_id: Mapped[UUID | None] = mapped_column(nullable=True)
    lead_technician_id: Mapped[UUID | None] = mapped_column(nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    vendor_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    maintenance_contract_id: Mapped[UUID | None] = mapped_column(nullable=True)
    warranty_id: Mapped[UUID | None] = mapped_column(nullable=True)
    planned_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    asset_condition_before: Mapped[str | None] = mapped_column(String(30))
    asset_condition_after: Mapped[str | None] = mapped_column(String(30))
    completion_summary: Mapped[str | None] = mapped_column(Text)
    resolution_code: Mapped[str | None] = mapped_column(String(30))
    requires_shutdown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_permit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_verification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by_employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=0, nullable=False
    )
    estimated_part_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=0, nullable=False
    )
    estimated_vendor_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=0, nullable=False
    )
    actual_labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=0, nullable=False
    )
    actual_part_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=0, nullable=False
    )
    actual_vendor_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=0, nullable=False
    )
    currency_code: Mapped[str | None] = mapped_column(String(3))
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    asset = relationship("Asset")
    priority: Mapped[MaintenancePriority] = relationship()
    vendor_partner = relationship("BusinessPartner")
    requests: Mapped[list[MaintenanceRequestWorkOrder]] = relationship(
        back_populates="work_order"
    )
    assignments: Mapped[list[MaintenanceWorkOrderAssignment]] = relationship(
        back_populates="work_order"
    )
    required_skills: Mapped[list[MaintenanceWorkOrderRequiredSkill]] = relationship(
        back_populates="work_order"
    )
    part_requirements: Mapped[list[MaintenancePartRequirement]] = relationship(
        back_populates="work_order"
    )
    vendor_personnel: Mapped[list[MaintenanceVendorPersonnel]] = relationship(
        back_populates="work_order"
    )
    failures: Mapped[list[AssetFailure]] = relationship(back_populates="work_order")
    part_usages: Mapped[list[MaintenancePartUsage]] = relationship(back_populates="work_order")
    labor_logs: Mapped[list[MaintenanceLaborLog]] = relationship(back_populates="work_order")
    downtimes: Mapped[list[MaintenanceDowntime]] = relationship(back_populates="work_order")
    events: Mapped[list[MaintenanceWorkOrderEvent]] = relationship(back_populates="work_order")


class MaintenanceSlaSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_sla_snapshots"

    maintenance_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    maintenance_contract_id: Mapped[UUID | None] = mapped_column(nullable=True)
    priority_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_priorities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    response_target_minutes: Mapped[int | None] = mapped_column(Integer)
    resolution_target_minutes: Mapped[int | None] = mapped_column(Integer)
    response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolution_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    snapshot_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="sla_snapshots")
    priority: Mapped[MaintenancePriority] = relationship()


class MaintenanceRequestWorkOrder(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_request_work_orders"
    __table_args__ = (
        UniqueConstraint(
            "maintenance_request_id",
            "work_order_id",
            name="uq_maintenance_request_work_orders_request_work_order",
        ),
    )

    maintenance_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(String(30), nullable=False)

    request: Mapped[MaintenanceRequest] = relationship(back_populates="work_orders")
    work_order: Mapped[MaintenanceWorkOrder] = relationship(back_populates="requests")


class MaintenanceWorkOrderAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_work_order_assignments"
    __table_args__ = (
        UniqueConstraint(
            "work_order_id",
            "employee_id",
            "assignment_role",
            name="uq_maintenance_work_order_assignments_unique",
        ),
    )

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[UUID] = mapped_column(nullable=False)
    assignment_role: Mapped[str] = mapped_column(String(30), nullable=False)
    planned_minutes: Mapped[int | None] = mapped_column(Integer)
    actual_minutes: Mapped[int | None] = mapped_column(Integer)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    work_order: Mapped[MaintenanceWorkOrder] = relationship(back_populates="assignments")


class MaintenancePartRequirement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_part_requirements"

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    part_item_id: Mapped[UUID] = mapped_column(nullable=False)
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        default=0,
        nullable=False,
    )
    issued_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        default=0,
        nullable=False,
    )
    returned_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 4),
        default=0,
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    requirement_status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    work_order: Mapped[MaintenanceWorkOrder] = relationship(
        back_populates="part_requirements"
    )


class MaintenanceVendorPersonnel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_vendor_personnel"

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    vendor_partner_id: Mapped[UUID] = mapped_column(
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    person_name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    technician_reference: Mapped[str | None] = mapped_column(String(100))
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    work_order: Mapped[MaintenanceWorkOrder] = relationship(
        back_populates="vendor_personnel"
    )
    vendor_partner = relationship("BusinessPartner")


class MaintenanceTeam(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_teams"
    __table_args__ = (
        UniqueConstraint("company_id", "team_code", name="uq_maintenance_teams_company_code"),
    )

    company_id: Mapped[UUID] = mapped_column(nullable=False)
    team_code: Mapped[str] = mapped_column(String(30), nullable=False)
    team_name: Mapped[str] = mapped_column(String(150), nullable=False)
    team_type: Mapped[str] = mapped_column(String(30), nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(nullable=True)
    supervisor_employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    default_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    default_location = relationship("AssetLocation")
    members: Mapped[list[MaintenanceTeamMember]] = relationship(back_populates="team")


class MaintenanceTeamMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_team_members"
    __table_args__ = (
        UniqueConstraint(
            "maintenance_team_id",
            "employee_id",
            "effective_from",
            name="uq_maintenance_team_members_team_employee_from",
        ),
    )

    maintenance_team_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[UUID] = mapped_column(nullable=False)
    member_role: Mapped[str] = mapped_column(String(30), nullable=False)
    skill_level: Mapped[str | None] = mapped_column(String(20))
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    team: Mapped[MaintenanceTeam] = relationship(back_populates="members")


class MaintenanceSkill(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_skills"

    skill_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(150), nullable=False)
    certification_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


class EmployeeMaintenanceSkill(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "employee_maintenance_skills"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "maintenance_skill_id",
            "valid_from",
            name="uq_employee_maintenance_skills_employee_skill_from",
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(nullable=False)
    maintenance_skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    proficiency_level: Mapped[str | None] = mapped_column(String(20))
    certificate_number: Mapped[str | None] = mapped_column(String(100))
    valid_from: Mapped[date | None] = mapped_column(nullable=True)
    valid_to: Mapped[date | None] = mapped_column(nullable=True)

    maintenance_skill: Mapped[MaintenanceSkill] = relationship()


class MaintenanceWorkOrderRequiredSkill(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_work_order_required_skills"
    __table_args__ = (
        UniqueConstraint(
            "work_order_id",
            "maintenance_skill_id",
            name="uq_maintenance_work_order_required_skills_unique",
        ),
    )

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    maintenance_skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    minimum_proficiency_level: Mapped[str | None] = mapped_column(String(20))
    certification_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    work_order: Mapped[MaintenanceWorkOrder] = relationship(
        back_populates="required_skills"
    )
    maintenance_skill: Mapped[MaintenanceSkill] = relationship()


class MaintenanceSchedule(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_schedules"

    schedule_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    maintenance_plan_id: Mapped[UUID | None] = mapped_column(nullable=True)
    maintenance_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="SET NULL")
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="SET NULL")
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    schedule_source: Mapped[str] = mapped_column(String(30), nullable=False)
    scheduled_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    maintenance_team_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_teams.id", ondelete="SET NULL")
    )
    vendor_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    maintenance_contract_id: Mapped[UUID | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reschedule_reason: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    asset = relationship("Asset")
    request = relationship("MaintenanceRequest")
    work_order = relationship("MaintenanceWorkOrder")
    maintenance_team = relationship("MaintenanceTeam")
    vendor_partner = relationship("BusinessPartner")


class MaintenancePlan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_plans"

    plan_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL")
    )
    asset_category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_categories.id", ondelete="SET NULL")
    )
    maintenance_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    calendar_interval_value: Mapped[int | None] = mapped_column(Integer)
    calendar_interval_unit: Mapped[str | None] = mapped_column(String(20))
    meter_id: Mapped[UUID | None] = mapped_column(nullable=True)
    meter_interval: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    condition_rule: Mapped[dict | None] = mapped_column(JSONB)
    default_priority_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_priorities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    default_team_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_teams.id", ondelete="SET NULL")
    )
    default_vendor_partner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("business_partners.id", ondelete="SET NULL")
    )
    maintenance_contract_id: Mapped[UUID | None] = mapped_column(nullable=True)
    checklist_template_id: Mapped[UUID | None] = mapped_column(nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    auto_create_request: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_create_work_order: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(nullable=True)
    next_due_meter_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    asset = relationship("Asset")
    asset_category = relationship("AssetCategory")
    default_priority = relationship("MaintenancePriority")
    default_team = relationship("MaintenanceTeam")
    default_vendor_partner = relationship("BusinessPartner")
    plan_assets: Mapped[list[MaintenancePlanAsset]] = relationship(back_populates="plan")


class MaintenancePlanAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_plan_assets"
    __table_args__ = (
        UniqueConstraint(
            "maintenance_plan_id",
            "asset_id",
            "effective_from",
            name="uq_maintenance_plan_assets_plan_asset_from",
        ),
    )

    maintenance_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    override_interval_value: Mapped[int | None] = mapped_column(Integer)
    override_interval_unit: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    plan: Mapped[MaintenancePlan] = relationship(back_populates="plan_assets")
    asset = relationship("Asset")


class MaintenanceChecklistTemplate(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_checklist_templates"

    template_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    template_name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_categories.id", ondelete="SET NULL")
    )
    maintenance_type: Mapped[str | None] = mapped_column(String(30))
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    asset_category = relationship("AssetCategory")
    items: Mapped[list[MaintenanceChecklistTemplateItem]] = relationship(
        back_populates="template"
    )


class MaintenanceChecklistTemplateItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_checklist_template_items"
    __table_args__ = (
        UniqueConstraint(
            "checklist_template_id",
            "sequence_no",
            name="uq_maintenance_checklist_template_items_template_sequence",
        ),
    )

    checklist_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_checklist_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str] = mapped_column(String(50), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    response_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    normal_min_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    normal_max_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    unit_of_measure: Mapped[str | None] = mapped_column(String(20))
    failure_response_rule: Mapped[str | None] = mapped_column(String(30))

    template: Mapped[MaintenanceChecklistTemplate] = relationship(back_populates="items")


class MaintenanceChecklistExecution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_checklist_executions"

    checklist_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_checklist_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="SET NULL")
    )
    maintenance_schedule_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_schedules.id", ondelete="SET NULL")
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    performed_by_employee_id: Mapped[UUID] = mapped_column(nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    overall_result: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    template: Mapped[MaintenanceChecklistTemplate] = relationship()
    work_order: Mapped[MaintenanceWorkOrder | None] = relationship()
    maintenance_schedule = relationship("MaintenanceSchedule")
    asset = relationship("Asset")
    results: Mapped[list[MaintenanceChecklistResult]] = relationship(
        back_populates="execution"
    )


class MaintenanceChecklistResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_checklist_results"
    __table_args__ = (
        UniqueConstraint(
            "checklist_execution_id",
            "template_item_id",
            name="uq_maintenance_checklist_results_execution_template_item",
        ),
    )

    checklist_execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_checklist_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_checklist_template_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    result_status: Mapped[str | None] = mapped_column(String(20))
    boolean_value: Mapped[bool | None] = mapped_column(Boolean)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    text_value: Mapped[str | None] = mapped_column(Text)
    meter_reading_id: Mapped[UUID | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    execution: Mapped[MaintenanceChecklistExecution] = relationship(back_populates="results")
    template_item: Mapped[MaintenanceChecklistTemplateItem] = relationship()
    findings: Mapped[list[MaintenanceFinding]] = relationship(back_populates="checklist_result")


class MaintenanceFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_findings"

    finding_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    checklist_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_checklist_results.id", ondelete="SET NULL")
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="SET NULL")
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    finding_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    requires_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_asset_shutdown: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    follow_up_due_date: Mapped[date | None] = mapped_column(nullable=True)
    generated_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reported_by_employee_id: Mapped[UUID] = mapped_column(nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    checklist_result: Mapped[MaintenanceChecklistResult | None] = relationship(
        back_populates="findings"
    )
    work_order: Mapped[MaintenanceWorkOrder | None] = relationship()
    asset = relationship("Asset")
    generated_request: Mapped[MaintenanceRequest | None] = relationship()


class MaintenanceSymptomCode(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_symptom_codes"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MaintenanceFailureMode(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_failure_modes"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MaintenanceRootCauseCode(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_root_cause_codes"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AssetFailure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_failures"

    failure_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    maintenance_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="SET NULL")
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="SET NULL")
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_by_employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    failure_mode_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_failure_modes.id", ondelete="SET NULL")
    )
    symptom_code_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_symptom_codes.id", ondelete="SET NULL")
    )
    failure_description: Mapped[str] = mapped_column(Text, nullable=False)
    failure_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_condition_before: Mapped[str | None] = mapped_column(String(30))
    asset_condition_after: Mapped[str | None] = mapped_column(String(30))
    caused_shutdown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_incident: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    repeat_failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    temporary_action: Mapped[str | None] = mapped_column(Text)
    root_cause_code_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_root_cause_codes.id", ondelete="SET NULL")
    )
    root_cause_description: Mapped[str | None] = mapped_column(Text)
    corrective_action: Mapped[str | None] = mapped_column(Text)
    preventive_action: Mapped[str | None] = mapped_column(Text)
    failure_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    downtime_minutes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)

    asset = relationship("Asset")
    maintenance_request: Mapped[MaintenanceRequest | None] = relationship()
    work_order: Mapped[MaintenanceWorkOrder | None] = relationship(back_populates="failures")
    failure_mode: Mapped[MaintenanceFailureMode | None] = relationship()
    symptom_code: Mapped[MaintenanceSymptomCode | None] = relationship()
    root_cause_code: Mapped[MaintenanceRootCauseCode | None] = relationship()


class MaintenancePartUsage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_part_usages"

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    part_item_id: Mapped[UUID] = mapped_column(nullable=False)
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    currency_code: Mapped[str | None] = mapped_column(String(3))
    usage_type: Mapped[str] = mapped_column(String(20), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_by_employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    sap_inventory_doc_entry: Mapped[int | None] = mapped_column(Integer)
    sap_inventory_doc_num: Mapped[int | None] = mapped_column(Integer)
    removed_component_asset_id: Mapped[UUID | None] = mapped_column(nullable=True)
    installed_component_asset_id: Mapped[UUID | None] = mapped_column(nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100))

    work_order: Mapped[MaintenanceWorkOrder] = relationship(back_populates="part_usages")
    asset = relationship("Asset")


class MaintenanceLaborLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_labor_logs"

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[UUID] = mapped_column(nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    labor_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    notes: Mapped[str | None] = mapped_column(Text)

    work_order: Mapped[MaintenanceWorkOrder] = relationship(back_populates="labor_logs")


class MaintenanceDowntime(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_downtimes"

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    maintenance_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_requests.id", ondelete="SET NULL")
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="SET NULL")
    )
    downtime_type: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    production_loss_quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    unit_of_measure: Mapped[str | None] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    asset = relationship("Asset")
    request: Mapped[MaintenanceRequest | None] = relationship()
    work_order: Mapped[MaintenanceWorkOrder | None] = relationship(back_populates="downtimes")


class MaintenanceWorkOrderEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_work_order_events"

    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str | None] = mapped_column(String(30))
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    performed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    employee_id: Mapped[UUID | None] = mapped_column(nullable=True)
    reason: Mapped[str | None] = mapped_column(Text)
    event_payload: Mapped[dict | None] = mapped_column(JSONB)

    work_order: Mapped[MaintenanceWorkOrder] = relationship(back_populates="events")
