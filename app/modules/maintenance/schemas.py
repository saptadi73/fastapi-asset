from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.schemas import AssetLocationRead
from app.modules.maintenance.constants import (
    ChecklistFailureResponseRule,
    ChecklistResponseType,
    ChecklistResultStatus,
    MaintenanceFindingSeverity,
    MaintenanceFindingType,
    MaintenancePlanTriggerType,
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


class MaintenanceChecklistTemplateItemCreate(BaseModel):
    sequence_no: int = Field(ge=1)
    item_code: str = Field(max_length=50)
    instruction: str
    response_type: ChecklistResponseType
    is_required: bool = True
    normal_min_value: Decimal | None = None
    normal_max_value: Decimal | None = None
    unit_of_measure: str | None = Field(default=None, max_length=20)
    failure_response_rule: ChecklistFailureResponseRule | None = None


class MaintenanceChecklistTemplateCreate(BaseModel):
    template_code: str = Field(max_length=50)
    template_name: str = Field(max_length=200)
    asset_category_id: UUID | None = None
    maintenance_type: MaintenanceType | None = None
    version_number: int = Field(default=1, ge=1)
    effective_from: date
    effective_to: date | None = None
    is_active: bool = True
    items: list[MaintenanceChecklistTemplateItemCreate]


class MaintenanceChecklistTemplateItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    checklist_template_id: UUID
    sequence_no: int
    item_code: str
    instruction: str
    response_type: str
    is_required: bool
    normal_min_value: Decimal | None
    normal_max_value: Decimal | None
    unit_of_measure: str | None
    failure_response_rule: str | None


class MaintenanceChecklistTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_code: str
    template_name: str
    asset_category_id: UUID | None
    maintenance_type: str | None
    version_number: int
    effective_from: date
    effective_to: date | None
    is_active: bool
    items: list[MaintenanceChecklistTemplateItemRead] = []


class MaintenanceChecklistExecutionStartPayload(BaseModel):
    checklist_template_id: UUID | None = None
    performed_by_employee_id: UUID
    started_at: datetime


class MaintenanceChecklistResultEntryCreate(BaseModel):
    template_item_id: UUID
    result_status: ChecklistResultStatus | None = None
    boolean_value: bool | None = None
    numeric_value: Decimal | None = None
    text_value: str | None = None
    meter_reading_id: UUID | None = None
    notes: str | None = None
    performed_at: datetime
    finding_type: MaintenanceFindingType | None = None
    finding_severity: MaintenanceFindingSeverity | None = None
    finding_description: str | None = None
    recommended_action: str | None = None
    requires_follow_up: bool = False
    requires_asset_shutdown: bool = False
    follow_up_due_date: date | None = None


class MaintenanceChecklistResultSubmitPayload(BaseModel):
    completed_at: datetime
    results: list[MaintenanceChecklistResultEntryCreate]


class MaintenanceFindingCreateRequestPayload(BaseModel):
    request_number: str = Field(max_length=50)
    priority_id: UUID
    reported_at: datetime
    title: str = Field(max_length=200)
    problem_description: str
    requested_vendor_partner_id: UUID | None = None
    required_response_at: datetime | None = None
    required_resolution_at: datetime | None = None
    created_by: UUID
    updated_by: UUID | None = None
    submit: bool = False


class MaintenanceFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    finding_number: str
    checklist_result_id: UUID | None
    work_order_id: UUID | None
    asset_id: UUID
    finding_type: str
    severity: str
    description: str
    recommended_action: str | None
    requires_follow_up: bool
    requires_asset_shutdown: bool
    follow_up_due_date: date | None
    generated_request_id: UUID | None
    status: str
    reported_by_employee_id: UUID
    reported_at: datetime
    resolved_at: datetime | None
    asset: MaintenanceAssetReferenceRead
    generated_request: MaintenanceRequestRead | None = None


class MaintenanceChecklistResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    checklist_execution_id: UUID
    template_item_id: UUID
    result_status: str | None
    boolean_value: bool | None
    numeric_value: Decimal | None
    text_value: str | None
    meter_reading_id: UUID | None
    notes: str | None
    performed_at: datetime
    template_item: MaintenanceChecklistTemplateItemRead
    findings: list[MaintenanceFindingRead] = []


class MaintenanceChecklistExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    checklist_template_id: UUID
    work_order_id: UUID | None
    maintenance_schedule_id: UUID | None
    asset_id: UUID
    performed_by_employee_id: UUID
    started_at: datetime
    completed_at: datetime | None
    overall_result: str | None
    status: str
    template: MaintenanceChecklistTemplateRead
    asset: MaintenanceAssetReferenceRead
    results: list[MaintenanceChecklistResultRead] = []


class MaintenancePlanCreate(BaseModel):
    plan_code: str = Field(max_length=50)
    plan_name: str = Field(max_length=200)
    asset_id: UUID | None = None
    asset_category_id: UUID | None = None
    maintenance_type: MaintenanceType
    trigger_type: MaintenancePlanTriggerType
    calendar_interval_value: int | None = Field(default=None, ge=1)
    calendar_interval_unit: str | None = Field(default=None, max_length=20)
    meter_id: UUID | None = None
    meter_interval: Decimal | None = None
    condition_rule: dict | None = None
    default_priority_id: UUID
    default_team_id: UUID | None = None
    default_vendor_partner_id: UUID | None = None
    maintenance_contract_id: UUID | None = None
    checklist_template_id: UUID | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    lead_time_days: int = Field(default=0, ge=0)
    auto_create_request: bool = False
    auto_create_work_order: bool = True
    requires_approval: bool = False
    effective_from: date
    effective_to: date | None = None
    next_due_date: date | None = None
    next_due_meter_value: Decimal | None = None
    is_active: bool = True


class MaintenancePlanAssetCreate(BaseModel):
    asset_id: UUID
    effective_from: date
    effective_to: date | None = None
    override_interval_value: int | None = Field(default=None, ge=1)
    override_interval_unit: str | None = Field(default=None, max_length=20)
    is_active: bool = True


class MaintenancePlanGeneratePayload(BaseModel):
    scheduled_start_at: datetime
    schedule_prefix: str = Field(default="SCH", max_length=20)
    created_by: UUID
    create_work_orders: bool | None = None


class MaintenancePlanAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    maintenance_plan_id: UUID
    asset_id: UUID
    effective_from: date
    effective_to: date | None
    override_interval_value: int | None
    override_interval_unit: str | None
    is_active: bool
    asset: MaintenanceAssetReferenceRead


class MaintenancePlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_code: str
    plan_name: str
    asset_id: UUID | None
    asset_category_id: UUID | None
    maintenance_type: str
    trigger_type: str
    calendar_interval_value: int | None
    calendar_interval_unit: str | None
    meter_id: UUID | None
    meter_interval: Decimal | None
    condition_rule: dict | None
    default_priority_id: UUID
    default_team_id: UUID | None
    default_vendor_partner_id: UUID | None
    maintenance_contract_id: UUID | None
    checklist_template_id: UUID | None
    estimated_duration_minutes: int | None
    lead_time_days: int
    auto_create_request: bool
    auto_create_work_order: bool
    requires_approval: bool
    effective_from: date
    effective_to: date | None
    next_due_date: date | None
    next_due_meter_value: Decimal | None
    is_active: bool
    asset: MaintenanceAssetReferenceRead | None = None
    default_priority: MaintenancePriorityRead
    default_team: MaintenanceTeamRead | None = None
    plan_assets: list[MaintenancePlanAssetRead] = []


class MaintenancePlanListItemRead(BaseModel):
    id: UUID
    plan_code: str
    plan_name: str
    maintenance_type: str
    trigger_type: str
    asset_id: UUID | None
    asset_category_id: UUID | None
    default_priority: MaintenancePriorityRead
    default_team: MaintenanceTeamRead | None = None
    is_active: bool
    plan_asset_count: int

    @classmethod
    def from_model(cls, item: object) -> MaintenancePlanListItemRead:
        return cls(
            id=item.id,
            plan_code=item.plan_code,
            plan_name=item.plan_name,
            maintenance_type=item.maintenance_type,
            trigger_type=item.trigger_type,
            asset_id=item.asset_id,
            asset_category_id=item.asset_category_id,
            default_priority=MaintenancePriorityRead.model_validate(item.default_priority),
            default_team=(
                MaintenanceTeamRead.model_validate(item.default_team)
                if getattr(item, "default_team", None)
                else None
            ),
            is_active=item.is_active,
            plan_asset_count=len(getattr(item, "plan_assets", [])),
        )


class AssetMaintenanceHistoryItemRead(BaseModel):
    work_order_id: UUID
    work_order_number: str
    maintenance_type: str
    status: str
    title: str
    planned_start_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None
    closed_at: datetime | None
    completion_summary: str | None
    asset_condition_before: str | None
    asset_condition_after: str | None
    priority: MaintenancePriorityRead

    @classmethod
    def from_model(cls, item: object) -> AssetMaintenanceHistoryItemRead:
        return cls(
            work_order_id=item.id,
            work_order_number=item.work_order_number,
            maintenance_type=item.maintenance_type,
            status=item.status,
            title=item.title,
            planned_start_at=item.planned_start_at,
            actual_start_at=item.actual_start_at,
            actual_end_at=item.actual_end_at,
            closed_at=item.closed_at,
            completion_summary=item.completion_summary,
            asset_condition_before=item.asset_condition_before,
            asset_condition_after=item.asset_condition_after,
            priority=MaintenancePriorityRead.model_validate(item.priority),
        )
