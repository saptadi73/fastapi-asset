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
