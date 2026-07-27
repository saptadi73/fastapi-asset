from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.schemas import AssetLocationRead
from app.modules.maintenance.constants import (
    MaintenanceRequestSourceType,
    MaintenanceRequestType,
    MaintenanceRequestWorkOrderRelationshipType,
    MaintenanceScheduleSource,
    MaintenanceTeamMemberRole,
    MaintenanceTeamType,
    MaintenanceType,
    WorkOrderAssignmentRole,
    WorkOrderExecutionMode,
)


class MaintenancePriorityCreate(BaseModel):
    code: str = Field(max_length=30)
    name: str = Field(max_length=100)
    severity_level: int = Field(ge=1, le=10)
    default_response_minutes: int | None = Field(default=None, ge=1)
    default_resolution_minutes: int | None = Field(default=None, ge=1)
    escalation_after_minutes: int | None = Field(default=None, ge=1)
    color_code: str | None = Field(default=None, max_length=20)
    is_emergency: bool = False
    is_active: bool = True


class MaintenancePriorityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    severity_level: int
    default_response_minutes: int | None
    default_resolution_minutes: int | None
    escalation_after_minutes: int | None
    color_code: str | None
    is_emergency: bool
    is_active: bool


class MaintenanceAssetReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_code: str
    asset_name: str
    asset_status: str
    condition_status: str
    current_location_id: UUID | None


class MaintenanceRequestCreate(BaseModel):
    request_number: str = Field(max_length=50)
    company_id: UUID
    asset_id: UUID
    parent_request_id: UUID | None = None
    request_type: MaintenanceRequestType
    source_type: MaintenanceRequestSourceType
    requested_by_employee_id: UUID | None = None
    reported_by_name: str | None = Field(default=None, max_length=150)
    reported_at: datetime
    title: str = Field(max_length=200)
    problem_description: str
    priority_id: UUID
    asset_location_id: UUID | None = None
    operating_condition: str | None = None
    is_asset_stopped: bool = False
    downtime_started_at: datetime | None = None
    safety_impact: bool = False
    environmental_impact: bool = False
    production_impact: bool = False
    maintenance_contract_id: UUID | None = None
    warranty_id: UUID | None = None
    requested_vendor_partner_id: UUID | None = None
    required_response_at: datetime | None = None
    required_resolution_at: datetime | None = None
    created_by: UUID
    updated_by: UUID | None = None


class MaintenanceRequestTriagePayload(BaseModel):
    actor_id: UUID
    acted_at: datetime
    priority_id: UUID | None = None
    asset_location_id: UUID | None = None
    operating_condition: str | None = None
    requested_vendor_partner_id: UUID | None = None
    required_response_at: datetime | None = None
    required_resolution_at: datetime | None = None


class MaintenanceRequestActionPayload(BaseModel):
    actor_id: UUID
    acted_at: datetime
    notes: str | None = None


class MaintenanceRequestRejectPayload(MaintenanceRequestActionPayload):
    rejection_reason: str


class MaintenanceWorkOrderCreate(BaseModel):
    work_order_number: str = Field(max_length=50)
    company_id: UUID
    asset_id: UUID
    maintenance_type: MaintenanceType
    priority_id: UUID
    title: str = Field(max_length=200)
    scope_of_work: str
    execution_mode: WorkOrderExecutionMode
    vendor_partner_id: UUID | None = None
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    asset_condition_before: str | None = Field(default=None, max_length=30)
    requires_shutdown: bool = False
    requires_permit: bool = False
    requires_verification: bool = True
    estimated_labor_cost: Decimal = Decimal("0")
    estimated_part_cost: Decimal = Decimal("0")
    estimated_vendor_cost: Decimal = Decimal("0")
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    created_by: UUID
    updated_by: UUID | None = None


class MaintenanceConvertToWorkOrderPayload(BaseModel):
    work_order_number: str = Field(max_length=50)
    maintenance_type: MaintenanceType
    execution_mode: WorkOrderExecutionMode
    scope_of_work: str
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    vendor_partner_id: UUID | None = None
    requires_shutdown: bool = False
    requires_permit: bool = False
    requires_verification: bool = True
    created_by: UUID
    updated_by: UUID | None = None
    relationship_type: MaintenanceRequestWorkOrderRelationshipType = (
        MaintenanceRequestWorkOrderRelationshipType.PRIMARY
    )


class MaintenanceWorkOrderAssignPayload(BaseModel):
    actor_id: UUID
    acted_at: datetime
    employee_id: UUID
    assignment_role: WorkOrderAssignmentRole
    planned_minutes: int | None = Field(default=None, ge=1)
    accepted_at: datetime | None = None


class MaintenanceWorkOrderCompletePayload(BaseModel):
    actor_id: UUID
    acted_at: datetime
    completion_summary: str
    asset_condition_after: str | None = Field(default=None, max_length=30)
    resolution_code: str | None = Field(default=None, max_length=30)
    actual_labor_cost: Decimal = Decimal("0")
    actual_part_cost: Decimal = Decimal("0")
    actual_vendor_cost: Decimal = Decimal("0")


class MaintenanceWorkOrderVerifyPayload(BaseModel):
    actor_id: UUID
    acted_at: datetime


class MaintenanceRequestWorkOrderLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    maintenance_request_id: UUID
    work_order_id: UUID
    relationship_type: str


class MaintenanceWorkOrderAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    employee_id: UUID
    assignment_role: str
    planned_minutes: int | None
    actual_minutes: int | None
    assigned_at: datetime
    accepted_at: datetime | None
    released_at: datetime | None


class MaintenanceRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_number: str
    company_id: UUID
    asset_id: UUID
    parent_request_id: UUID | None
    request_type: str
    source_type: str
    requested_by_employee_id: UUID | None
    reported_by_name: str | None
    reported_at: datetime
    title: str
    problem_description: str
    priority_id: UUID
    asset_location_id: UUID | None
    operating_condition: str | None
    is_asset_stopped: bool
    downtime_started_at: datetime | None
    safety_impact: bool
    environmental_impact: bool
    production_impact: bool
    maintenance_contract_id: UUID | None
    warranty_id: UUID | None
    requested_vendor_partner_id: UUID | None
    status: str
    triaged_by_employee_id: UUID | None
    triaged_at: datetime | None
    rejection_reason: str | None
    cancellation_reason: str | None
    required_response_at: datetime | None
    required_resolution_at: datetime | None
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID | None
    version: int
    asset: MaintenanceAssetReferenceRead
    priority: MaintenancePriorityRead
    asset_location: AssetLocationRead | None = None
    work_orders: list[MaintenanceRequestWorkOrderLinkRead] = []


class MaintenanceRequestListItemRead(BaseModel):
    id: UUID
    request_number: str
    asset_id: UUID
    title: str
    request_type: str
    status: str
    reported_at: datetime
    priority: MaintenancePriorityRead
    asset: MaintenanceAssetReferenceRead

    @classmethod
    def from_model(cls, item: object) -> MaintenanceRequestListItemRead:
        return cls(
            id=item.id,
            request_number=item.request_number,
            asset_id=item.asset_id,
            title=item.title,
            request_type=item.request_type,
            status=item.status,
            reported_at=item.reported_at,
            priority=MaintenancePriorityRead.model_validate(item.priority),
            asset=MaintenanceAssetReferenceRead.model_validate(item.asset),
        )


class MaintenanceWorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_number: str
    company_id: UUID
    asset_id: UUID
    maintenance_type: str
    priority_id: UUID
    title: str
    scope_of_work: str
    execution_mode: str
    vendor_partner_id: UUID | None
    planned_start_at: datetime | None
    planned_end_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None
    asset_condition_before: str | None
    asset_condition_after: str | None
    completion_summary: str | None
    resolution_code: str | None
    requires_shutdown: bool
    requires_permit: bool
    requires_verification: bool
    status: str
    approved_by: UUID | None
    approved_at: datetime | None
    verified_by_employee_id: UUID | None
    verified_at: datetime | None
    closed_by: UUID | None
    closed_at: datetime | None
    estimated_labor_cost: Decimal
    estimated_part_cost: Decimal
    estimated_vendor_cost: Decimal
    actual_labor_cost: Decimal
    actual_part_cost: Decimal
    actual_vendor_cost: Decimal
    currency_code: str | None
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID | None
    version: int
    asset: MaintenanceAssetReferenceRead
    priority: MaintenancePriorityRead
    requests: list[MaintenanceRequestWorkOrderLinkRead] = []
    assignments: list[MaintenanceWorkOrderAssignmentRead] = []


class MaintenanceWorkOrderListItemRead(BaseModel):
    id: UUID
    work_order_number: str
    asset_id: UUID
    title: str
    maintenance_type: str
    status: str
    planned_start_at: datetime | None
    actual_start_at: datetime | None
    priority: MaintenancePriorityRead
    asset: MaintenanceAssetReferenceRead

    @classmethod
    def from_model(cls, item: object) -> MaintenanceWorkOrderListItemRead:
        return cls(
            id=item.id,
            work_order_number=item.work_order_number,
            asset_id=item.asset_id,
            title=item.title,
            maintenance_type=item.maintenance_type,
            status=item.status,
            planned_start_at=item.planned_start_at,
            actual_start_at=item.actual_start_at,
            priority=MaintenancePriorityRead.model_validate(item.priority),
            asset=MaintenanceAssetReferenceRead.model_validate(item.asset),
        )


class MaintenanceTeamCreate(BaseModel):
    company_id: UUID
    team_code: str = Field(max_length=30)
    team_name: str = Field(max_length=150)
    team_type: MaintenanceTeamType
    department_id: UUID | None = None
    supervisor_employee_id: UUID | None = None
    default_location_id: UUID | None = None
    is_active: bool = True


class MaintenanceTeamMemberCreate(BaseModel):
    employee_id: UUID
    member_role: MaintenanceTeamMemberRole
    skill_level: str | None = Field(default=None, max_length=20)
    effective_from: date
    effective_to: date | None = None
    is_primary: bool = False


class MaintenanceTeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    maintenance_team_id: UUID
    employee_id: UUID
    member_role: str
    skill_level: str | None
    effective_from: date
    effective_to: date | None
    is_primary: bool


class MaintenanceTeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    team_code: str
    team_name: str
    team_type: str
    department_id: UUID | None
    supervisor_employee_id: UUID | None
    default_location_id: UUID | None
    is_active: bool
    default_location: AssetLocationRead | None = None
    members: list[MaintenanceTeamMemberRead] = []


class MaintenanceTeamListItemRead(BaseModel):
    id: UUID
    company_id: UUID
    team_code: str
    team_name: str
    team_type: str
    default_location_id: UUID | None
    is_active: bool
    member_count: int
    default_location: AssetLocationRead | None = None

    @classmethod
    def from_model(cls, item: object) -> MaintenanceTeamListItemRead:
        return cls(
            id=item.id,
            company_id=item.company_id,
            team_code=item.team_code,
            team_name=item.team_name,
            team_type=item.team_type,
            default_location_id=item.default_location_id,
            is_active=item.is_active,
            member_count=len(getattr(item, "members", [])),
            default_location=(
                AssetLocationRead.model_validate(item.default_location)
                if getattr(item, "default_location", None)
                else None
            ),
        )


class MaintenanceScheduleCreate(BaseModel):
    schedule_number: str = Field(max_length=50)
    maintenance_plan_id: UUID | None = None
    maintenance_request_id: UUID | None = None
    work_order_id: UUID | None = None
    asset_id: UUID
    schedule_source: MaintenanceScheduleSource
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    maintenance_team_id: UUID | None = None
    vendor_partner_id: UUID | None = None
    maintenance_contract_id: UUID | None = None
    created_by: UUID
    created_at: datetime


class MaintenanceScheduleReschedulePayload(BaseModel):
    actor_id: UUID
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    reschedule_reason: str


class MaintenanceScheduleConfirmPayload(BaseModel):
    actor_id: UUID
    acted_at: datetime


class MaintenanceScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    schedule_number: str
    maintenance_plan_id: UUID | None
    maintenance_request_id: UUID | None
    work_order_id: UUID | None
    asset_id: UUID
    schedule_source: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    maintenance_team_id: UUID | None
    vendor_partner_id: UUID | None
    maintenance_contract_id: UUID | None
    status: str
    reschedule_count: int
    reschedule_reason: str | None
    confirmed_at: datetime | None
    created_by: UUID
    created_at: datetime
    asset: MaintenanceAssetReferenceRead
    request: MaintenanceRequestRead | None = None
    work_order: MaintenanceWorkOrderRead | None = None
    maintenance_team: MaintenanceTeamRead | None = None


class MaintenanceScheduleListItemRead(BaseModel):
    id: UUID
    schedule_number: str
    asset_id: UUID
    maintenance_request_id: UUID | None
    work_order_id: UUID | None
    schedule_source: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    maintenance_team_id: UUID | None
    vendor_partner_id: UUID | None
    status: str
    reschedule_count: int
    confirmed_at: datetime | None
    asset: MaintenanceAssetReferenceRead
    maintenance_team: MaintenanceTeamRead | None = None

    @classmethod
    def from_model(cls, item: object) -> MaintenanceScheduleListItemRead:
        return cls(
            id=item.id,
            schedule_number=item.schedule_number,
            asset_id=item.asset_id,
            maintenance_request_id=item.maintenance_request_id,
            work_order_id=item.work_order_id,
            schedule_source=item.schedule_source,
            scheduled_start_at=item.scheduled_start_at,
            scheduled_end_at=item.scheduled_end_at,
            maintenance_team_id=item.maintenance_team_id,
            vendor_partner_id=item.vendor_partner_id,
            status=item.status,
            reschedule_count=item.reschedule_count,
            confirmed_at=item.confirmed_at,
            asset=MaintenanceAssetReferenceRead.model_validate(item.asset),
            maintenance_team=(
                MaintenanceTeamRead.model_validate(item.maintenance_team)
                if getattr(item, "maintenance_team", None)
                else None
            ),
        )
