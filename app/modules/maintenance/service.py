from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.assets.constants import AssetStatus, ConditionStatus
from app.modules.assets.exceptions import AssetLocationNotFoundError, AssetNotFoundError
from app.modules.assets.models import AssetStatusHistory
from app.modules.assets.repository import (
    AssetLocationRepository,
    AssetRepository,
    AssetStatusHistoryRepository,
)
from app.modules.maintenance.constants import (
    ChecklistExecutionStatus,
    ChecklistFailureResponseRule,
    ChecklistOverallResult,
    ChecklistResponseType,
    ChecklistResultStatus,
    MaintenanceFindingSeverity,
    MaintenanceFindingStatus,
    MaintenanceFindingType,
    MaintenancePartUsageType,
    MaintenancePlanTriggerType,
    MaintenanceRequestSourceType,
    MaintenanceRequestStatus,
    MaintenanceRequestType,
    MaintenanceScheduleStatus,
    MaintenanceWorkOrderEventType,
    MaintenanceWorkOrderStatus,
)
from app.modules.maintenance.exceptions import (
    MaintenanceAssetFailureNotFoundError,
    MaintenanceChecklistExecutionNotFoundError,
    MaintenanceChecklistTemplateNotFoundError,
    MaintenanceFailureModeNotFoundError,
    MaintenanceFindingNotFoundError,
    MaintenancePriorityNotFoundError,
    MaintenanceRequestNotFoundError,
    MaintenanceRootCauseCodeNotFoundError,
    MaintenanceScheduleNotFoundError,
    MaintenanceSymptomCodeNotFoundError,
    MaintenanceTeamNotFoundError,
    MaintenanceWorkOrderNotFoundError,
)
from app.modules.maintenance.models import (
    AssetFailure,
    MaintenanceChecklistExecution,
    MaintenanceChecklistResult,
    MaintenanceChecklistTemplate,
    MaintenanceChecklistTemplateItem,
    MaintenanceDowntime,
    MaintenanceFailureMode,
    MaintenanceFinding,
    MaintenanceLaborLog,
    MaintenancePartUsage,
    MaintenancePlan,
    MaintenancePlanAsset,
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceRequestWorkOrder,
    MaintenanceRootCauseCode,
    MaintenanceSchedule,
    MaintenanceSymptomCode,
    MaintenanceTeam,
    MaintenanceTeamMember,
    MaintenanceWorkOrder,
    MaintenanceWorkOrderAssignment,
    MaintenanceWorkOrderEvent,
)
from app.modules.maintenance.repository import (
    AssetFailureRepository,
    MaintenanceChecklistExecutionRepository,
    MaintenanceChecklistResultRepository,
    MaintenanceChecklistTemplateItemRepository,
    MaintenanceChecklistTemplateRepository,
    MaintenanceDowntimeRepository,
    MaintenanceFailureModeRepository,
    MaintenanceFindingRepository,
    MaintenanceLaborLogRepository,
    MaintenancePartUsageRepository,
    MaintenancePlanAssetRepository,
    MaintenancePlanRepository,
    MaintenancePriorityRepository,
    MaintenanceReportRepository,
    MaintenanceRequestRepository,
    MaintenanceRequestWorkOrderRepository,
    MaintenanceRootCauseCodeRepository,
    MaintenanceScheduleRepository,
    MaintenanceSymptomCodeRepository,
    MaintenanceTeamMemberRepository,
    MaintenanceTeamRepository,
    MaintenanceWorkOrderAssignmentRepository,
    MaintenanceWorkOrderEventRepository,
    MaintenanceWorkOrderRepository,
)
from app.modules.maintenance.schemas import (
    AssetFailureCreate,
    AssetFailureUpdate,
    AssetMaintenanceHistoryItemRead,
    MaintenanceBacklogReportRead,
    MaintenanceChecklistExecutionStartPayload,
    MaintenanceChecklistResultEntryCreate,
    MaintenanceChecklistResultSubmitPayload,
    MaintenanceChecklistTemplateCreate,
    MaintenanceConvertToWorkOrderPayload,
    MaintenanceCostReportItemRead,
    MaintenanceDowntimeCreate,
    MaintenanceFailureAnalysisAssetRead,
    MaintenanceFailureAnalysisBucketRead,
    MaintenanceFailureAnalysisReportRead,
    MaintenanceFindingCreateRequestPayload,
    MaintenanceLaborLogCreate,
    MaintenanceMasterCodeCreate,
    MaintenancePartUsageCreate,
    MaintenancePlanAssetCreate,
    MaintenancePlanCreate,
    MaintenancePlanGeneratePayload,
    MaintenancePriorityCreate,
    MaintenanceReliabilityReportRead,
    MaintenanceRequestActionPayload,
    MaintenanceRequestCreate,
    MaintenanceRequestRejectPayload,
    MaintenanceRequestTriagePayload,
    MaintenanceScheduleConfirmPayload,
    MaintenanceScheduleCreate,
    MaintenanceScheduleReschedulePayload,
    MaintenanceSlaReportRead,
    MaintenanceTeamCreate,
    MaintenanceTeamMemberCreate,
    MaintenanceWorkOrderAssignPayload,
    MaintenanceWorkOrderCompletePayload,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderVerifyPayload,
)
from app.modules.partners.exceptions import BusinessPartnerNotFoundError
from app.modules.partners.repository import BusinessPartnerRepository
from app.shared.pagination import PaginationParams


class MaintenanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.priorities = MaintenancePriorityRepository(session)
        self.plans = MaintenancePlanRepository(session)
        self.plan_assets = MaintenancePlanAssetRepository(session)
        self.checklist_templates = MaintenanceChecklistTemplateRepository(session)
        self.checklist_template_items = MaintenanceChecklistTemplateItemRepository(session)
        self.checklist_executions = MaintenanceChecklistExecutionRepository(session)
        self.checklist_results = MaintenanceChecklistResultRepository(session)
        self.downtimes = MaintenanceDowntimeRepository(session)
        self.findings = MaintenanceFindingRepository(session)
        self.symptom_codes = MaintenanceSymptomCodeRepository(session)
        self.failure_modes = MaintenanceFailureModeRepository(session)
        self.root_cause_codes = MaintenanceRootCauseCodeRepository(session)
        self.failures = AssetFailureRepository(session)
        self.part_usages = MaintenancePartUsageRepository(session)
        self.labor_logs = MaintenanceLaborLogRepository(session)
        self.events = MaintenanceWorkOrderEventRepository(session)
        self.reports = MaintenanceReportRepository(session)
        self.requests = MaintenanceRequestRepository(session)
        self.work_orders = MaintenanceWorkOrderRepository(session)
        self.request_work_orders = MaintenanceRequestWorkOrderRepository(session)
        self.assignments = MaintenanceWorkOrderAssignmentRepository(session)
        self.teams = MaintenanceTeamRepository(session)
        self.team_members = MaintenanceTeamMemberRepository(session)
        self.schedules = MaintenanceScheduleRepository(session)
        self.assets = AssetRepository(session)
        self.asset_locations = AssetLocationRepository(session)
        self.asset_status_histories = AssetStatusHistoryRepository(session)
        self.partners = BusinessPartnerRepository(session)

    async def create_symptom_code(
        self,
        payload: MaintenanceMasterCodeCreate,
    ) -> MaintenanceSymptomCode:
        item = MaintenanceSymptomCode(**payload.model_dump())
        try:
            await self.symptom_codes.create(item)
            await self.session.commit()
            await self.session.refresh(item)
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_SYMPTOM_CODE_CONFLICT",
                message="Maintenance symptom code sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return item

    async def list_symptom_codes(self) -> list[MaintenanceSymptomCode]:
        return list(await self.symptom_codes.list())

    async def create_failure_mode(
        self,
        payload: MaintenanceMasterCodeCreate,
    ) -> MaintenanceFailureMode:
        item = MaintenanceFailureMode(**payload.model_dump())
        try:
            await self.failure_modes.create(item)
            await self.session.commit()
            await self.session.refresh(item)
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_FAILURE_MODE_CONFLICT",
                message="Maintenance failure mode sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return item

    async def list_failure_modes(self) -> list[MaintenanceFailureMode]:
        return list(await self.failure_modes.list())

    async def create_root_cause_code(
        self,
        payload: MaintenanceMasterCodeCreate,
    ) -> MaintenanceRootCauseCode:
        item = MaintenanceRootCauseCode(**payload.model_dump())
        try:
            await self.root_cause_codes.create(item)
            await self.session.commit()
            await self.session.refresh(item)
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_ROOT_CAUSE_CODE_CONFLICT",
                message="Maintenance root cause code sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return item

    async def list_root_cause_codes(self) -> list[MaintenanceRootCauseCode]:
        return list(await self.root_cause_codes.list())

    async def create_plan(self, payload: MaintenancePlanCreate) -> MaintenancePlan:
        if payload.asset_id is None and payload.asset_category_id is None:
            raise AppError(
                code="MAINTENANCE_PLAN_SCOPE_REQUIRED",
                message="Maintenance plan harus memiliki asset_id atau asset_category_id.",
                status_code=422,
            )
        if payload.trigger_type == MaintenancePlanTriggerType.CALENDAR and (
            payload.calendar_interval_value is None or payload.calendar_interval_unit is None
        ):
            raise AppError(
                code="MAINTENANCE_PLAN_TRIGGER_INVALID",
                message=(
                    "Calendar plan harus memiliki calendar_interval_value dan "
                    "calendar_interval_unit."
                ),
                status_code=422,
            )
        if payload.asset_id is not None:
            await self._get_asset_or_raise(payload.asset_id)
        if payload.default_team_id is not None:
            await self.get_team(payload.default_team_id)
        await self._get_priority_or_raise(payload.default_priority_id)
        if payload.default_vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.default_vendor_partner_id)
        if payload.effective_to is not None and payload.effective_to < payload.effective_from:
            raise AppError(
                code="MAINTENANCE_PLAN_PERIOD_INVALID",
                message="effective_to tidak boleh lebih kecil dari effective_from.",
                status_code=422,
            )
        item = MaintenancePlan(
            plan_code=payload.plan_code,
            plan_name=payload.plan_name,
            asset_id=payload.asset_id,
            asset_category_id=payload.asset_category_id,
            maintenance_type=payload.maintenance_type.value,
            trigger_type=payload.trigger_type.value,
            calendar_interval_value=payload.calendar_interval_value,
            calendar_interval_unit=payload.calendar_interval_unit,
            meter_id=payload.meter_id,
            meter_interval=payload.meter_interval,
            condition_rule=payload.condition_rule,
            default_priority_id=payload.default_priority_id,
            default_team_id=payload.default_team_id,
            default_vendor_partner_id=payload.default_vendor_partner_id,
            maintenance_contract_id=payload.maintenance_contract_id,
            checklist_template_id=payload.checklist_template_id,
            estimated_duration_minutes=payload.estimated_duration_minutes,
            lead_time_days=payload.lead_time_days,
            auto_create_request=payload.auto_create_request,
            auto_create_work_order=payload.auto_create_work_order,
            requires_approval=payload.requires_approval,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            next_due_date=payload.next_due_date,
            next_due_meter_value=payload.next_due_meter_value,
            is_active=payload.is_active,
        )
        try:
            await self.plans.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_PLAN_CONFLICT",
                message="Plan code sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_plan(item.id)

    async def list_plans(self, pagination: PaginationParams) -> tuple[list[MaintenancePlan], int]:
        items, total_items = await self.plans.list(pagination)
        return list(items), total_items

    async def get_plan(self, plan_id) -> MaintenancePlan:
        item = await self.plans.get(plan_id)
        if item is None:
            raise AppError(
                code="MAINTENANCE_PLAN_NOT_FOUND",
                message="Maintenance plan tidak ditemukan.",
                status_code=404,
                details={"plan_id": str(plan_id)},
            )
        return item

    async def add_plan_asset(
        self,
        plan_id,
        payload: MaintenancePlanAssetCreate,
    ) -> MaintenancePlan:
        plan = await self.get_plan(plan_id)
        await self._get_asset_or_raise(payload.asset_id)
        if payload.effective_to is not None and payload.effective_to < payload.effective_from:
            raise AppError(
                code="MAINTENANCE_PLAN_ASSET_PERIOD_INVALID",
                message="effective_to tidak boleh lebih kecil dari effective_from.",
                status_code=422,
            )
        item = MaintenancePlanAsset(
            maintenance_plan_id=plan.id,
            asset_id=payload.asset_id,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            override_interval_value=payload.override_interval_value,
            override_interval_unit=payload.override_interval_unit,
            is_active=payload.is_active,
        )
        try:
            await self.plan_assets.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_PLAN_ASSET_CONFLICT",
                message="Asset sudah terdaftar pada plan dengan periode efektif yang sama.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_plan(plan_id)

    async def generate_schedules_from_plan(
        self,
        plan_id,
        payload: MaintenancePlanGeneratePayload,
    ) -> list[MaintenanceSchedule]:
        plan = await self.get_plan(plan_id)
        target_assets: list[tuple[UUID, int | None, str | None]] = []
        if plan.asset_id is not None:
            target_assets.append(
                (plan.asset_id, plan.calendar_interval_value, plan.calendar_interval_unit)
            )
        for plan_asset in await self.plan_assets.list_active_by_plan(plan.id):
            target_assets.append(
                (
                    plan_asset.asset_id,
                    plan_asset.override_interval_value or plan.calendar_interval_value,
                    plan_asset.override_interval_unit or plan.calendar_interval_unit,
                )
            )
        # Deduplicate while preserving order
        seen_asset_ids: set[UUID] = set()
        normalized_targets: list[tuple[UUID, int | None, str | None]] = []
        for asset_id, interval_value, interval_unit in target_assets:
            if asset_id not in seen_asset_ids:
                normalized_targets.append((asset_id, interval_value, interval_unit))
                seen_asset_ids.add(asset_id)
        if not normalized_targets:
            raise AppError(
                code="MAINTENANCE_PLAN_TARGETS_EMPTY",
                message="Maintenance plan belum memiliki asset target untuk digenerate.",
                status_code=422,
            )

        created_ids: list[UUID] = []
        try:
            for index, (asset_id, _, _) in enumerate(normalized_targets, start=1):
                asset = await self._get_asset_or_raise(asset_id)
                start_at = payload.scheduled_start_at
                duration_minutes = plan.estimated_duration_minutes or 60
                end_at = start_at + timedelta(minutes=duration_minutes)
                await self._ensure_schedule_no_conflict(
                    asset_id=asset_id,
                    scheduled_start_at=start_at,
                    scheduled_end_at=end_at,
                    maintenance_team_id=plan.default_team_id,
                    vendor_partner_id=plan.default_vendor_partner_id,
                    error_code="MAINTENANCE_PLAN_GENERATION_CONFLICT",
                )
                schedule = MaintenanceSchedule(
                    schedule_number=f"{payload.schedule_prefix}-{plan.plan_code}-{index:03d}",
                    maintenance_plan_id=plan.id,
                    maintenance_request_id=None,
                    work_order_id=None,
                    asset_id=asset_id,
                    schedule_source="PREVENTIVE_PLAN",
                    scheduled_start_at=start_at,
                    scheduled_end_at=end_at,
                    maintenance_team_id=plan.default_team_id,
                    vendor_partner_id=plan.default_vendor_partner_id,
                    maintenance_contract_id=plan.maintenance_contract_id,
                    status=MaintenanceScheduleStatus.PLANNED.value,
                    created_by=payload.created_by,
                    created_at=datetime.now(UTC if start_at.tzinfo else None),
                )
                created = await self.schedules.create(schedule)
                created_ids.append(created.id)

                if payload.create_work_orders is True or (
                    payload.create_work_orders is None and plan.auto_create_work_order
                ):
                    work_order = MaintenanceWorkOrder(
                        work_order_number=f"WO-{plan.plan_code}-{index:03d}",
                        company_id=asset.company_id,
                        asset_id=asset_id,
                        maintenance_type=plan.maintenance_type,
                        priority_id=plan.default_priority_id,
                        title=plan.plan_name,
                        scope_of_work=f"Generated from plan {plan.plan_code}.",
                        maintenance_plan_id=plan.id,
                        maintenance_team_id=plan.default_team_id,
                        execution_mode="INTERNAL"
                        if plan.default_vendor_partner_id is None
                        else "VENDOR",
                        vendor_partner_id=plan.default_vendor_partner_id,
                        maintenance_contract_id=plan.maintenance_contract_id,
                        planned_start_at=start_at,
                        planned_end_at=end_at,
                        requires_verification=True,
                        status=(
                            MaintenanceWorkOrderStatus.WAITING_APPROVAL.value
                            if plan.requires_approval
                            else MaintenanceWorkOrderStatus.APPROVED.value
                        ),
                        created_by=payload.created_by,
                        updated_by=payload.created_by,
                    )
                    created_wo = await self.work_orders.create(work_order)
                    await self.schedules.update(created, work_order_id=created_wo.id)

            if plan.trigger_type.startswith("CALENDAR") and plan.next_due_date is not None:
                next_due_date = plan.next_due_date
                if plan.calendar_interval_value and plan.calendar_interval_unit:
                    next_due_date = self._increment_due_date(
                        plan.next_due_date,
                        plan.calendar_interval_value,
                        plan.calendar_interval_unit,
                    )
                await self.plans.update(plan, next_due_date=next_due_date)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_PLAN_GENERATION_CONFLICT",
                message="Generate schedule dari plan menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        items = [await self.get_schedule(schedule_id) for schedule_id in created_ids]
        return items

    async def create_team(self, payload: MaintenanceTeamCreate) -> MaintenanceTeam:
        if payload.default_location_id is not None:
            await self._get_location_or_raise(payload.default_location_id)
        item = MaintenanceTeam(
            company_id=payload.company_id,
            team_code=payload.team_code,
            team_name=payload.team_name,
            team_type=payload.team_type.value,
            department_id=payload.department_id,
            supervisor_employee_id=payload.supervisor_employee_id,
            default_location_id=payload.default_location_id,
            is_active=payload.is_active,
        )
        try:
            await self.teams.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_TEAM_CONFLICT",
                message="Team code sudah digunakan pada company yang sama.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_team(item.id)

    async def list_teams(self, pagination: PaginationParams) -> tuple[list[MaintenanceTeam], int]:
        items, total_items = await self.teams.list(pagination)
        return list(items), total_items

    async def get_team(self, team_id) -> MaintenanceTeam:
        item = await self.teams.get(team_id)
        if item is None:
            raise MaintenanceTeamNotFoundError(str(team_id))
        return item

    async def add_team_member(
        self,
        team_id,
        payload: MaintenanceTeamMemberCreate,
    ) -> MaintenanceTeam:
        team = await self.get_team(team_id)
        if payload.effective_to is not None and payload.effective_to < payload.effective_from:
            raise AppError(
                code="MAINTENANCE_TEAM_MEMBER_PERIOD_INVALID",
                message="effective_to tidak boleh lebih kecil dari effective_from.",
                status_code=422,
            )
        item = MaintenanceTeamMember(
            maintenance_team_id=team.id,
            employee_id=payload.employee_id,
            member_role=payload.member_role.value,
            skill_level=payload.skill_level,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            is_primary=payload.is_primary,
        )
        try:
            await self.team_members.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_TEAM_MEMBER_CONFLICT",
                message="Member tim dengan periode efektif yang sama sudah ada.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_team(team_id)

    async def create_schedule(self, payload: MaintenanceScheduleCreate) -> MaintenanceSchedule:
        await self._get_asset_or_raise(payload.asset_id)
        if payload.maintenance_request_id is not None:
            await self.get_request(payload.maintenance_request_id)
        if payload.work_order_id is not None:
            await self.get_work_order(payload.work_order_id)
        if payload.maintenance_team_id is not None:
            await self.get_team(payload.maintenance_team_id)
        if payload.vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.vendor_partner_id)
        self._validate_schedule_window(payload.scheduled_start_at, payload.scheduled_end_at)
        await self._ensure_schedule_no_conflict(
            asset_id=payload.asset_id,
            scheduled_start_at=payload.scheduled_start_at,
            scheduled_end_at=payload.scheduled_end_at,
            maintenance_team_id=payload.maintenance_team_id,
            vendor_partner_id=payload.vendor_partner_id,
        )
        item = MaintenanceSchedule(
            schedule_number=payload.schedule_number,
            maintenance_plan_id=payload.maintenance_plan_id,
            maintenance_request_id=payload.maintenance_request_id,
            work_order_id=payload.work_order_id,
            asset_id=payload.asset_id,
            schedule_source=payload.schedule_source.value,
            scheduled_start_at=payload.scheduled_start_at,
            scheduled_end_at=payload.scheduled_end_at,
            maintenance_team_id=payload.maintenance_team_id,
            vendor_partner_id=payload.vendor_partner_id,
            maintenance_contract_id=payload.maintenance_contract_id,
            status=MaintenanceScheduleStatus.PLANNED.value,
            created_by=payload.created_by,
            created_at=payload.created_at,
        )
        try:
            await self.schedules.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_SCHEDULE_CONFLICT",
                message="Schedule number sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_schedule(item.id)

    async def list_schedules(
        self,
        pagination: PaginationParams,
    ) -> tuple[list[MaintenanceSchedule], int]:
        items, total_items = await self.schedules.list(pagination)
        return list(items), total_items

    async def get_schedule(self, schedule_id) -> MaintenanceSchedule:
        item = await self.schedules.get(schedule_id)
        if item is None:
            raise MaintenanceScheduleNotFoundError(str(schedule_id))
        return item

    async def confirm_schedule(
        self,
        schedule_id,
        payload: MaintenanceScheduleConfirmPayload,
    ) -> MaintenanceSchedule:
        item = await self.get_schedule(schedule_id)
        if item.status != MaintenanceScheduleStatus.PLANNED.value:
            raise AppError(
                code="MAINTENANCE_SCHEDULE_INVALID_STATUS",
                message="Hanya schedule PLANNED yang dapat dikonfirmasi.",
                status_code=409,
            )
        try:
            await self.schedules.update(
                item,
                status=MaintenanceScheduleStatus.CONFIRMED.value,
                confirmed_at=payload.acted_at,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_schedule(schedule_id)

    async def reschedule(
        self,
        schedule_id,
        payload: MaintenanceScheduleReschedulePayload,
    ) -> MaintenanceSchedule:
        item = await self.get_schedule(schedule_id)
        if item.status in {
            MaintenanceScheduleStatus.COMPLETED.value,
            MaintenanceScheduleStatus.CANCELLED.value,
        }:
            raise AppError(
                code="MAINTENANCE_SCHEDULE_INVALID_STATUS",
                message="Schedule yang sudah final tidak dapat di-reschedule.",
                status_code=409,
            )
        self._validate_schedule_window(payload.scheduled_start_at, payload.scheduled_end_at)
        await self._ensure_schedule_no_conflict(
            asset_id=item.asset_id,
            scheduled_start_at=payload.scheduled_start_at,
            scheduled_end_at=payload.scheduled_end_at,
            maintenance_team_id=item.maintenance_team_id,
            vendor_partner_id=item.vendor_partner_id,
            exclude_schedule_id=item.id,
        )
        try:
            await self.schedules.update(
                item,
                scheduled_start_at=payload.scheduled_start_at,
                scheduled_end_at=payload.scheduled_end_at,
                status=MaintenanceScheduleStatus.POSTPONED.value,
                reschedule_count=item.reschedule_count + 1,
                reschedule_reason=payload.reschedule_reason,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_schedule(schedule_id)

    async def create_priority(self, payload: MaintenancePriorityCreate) -> MaintenancePriority:
        item = MaintenancePriority(**payload.model_dump())
        try:
            await self.priorities.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_PRIORITY_CONFLICT",
                message="Code maintenance priority sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return item

    async def list_priorities(self) -> list[MaintenancePriority]:
        return list(await self.priorities.list())

    async def create_checklist_template(
        self,
        payload: MaintenanceChecklistTemplateCreate,
    ) -> MaintenanceChecklistTemplate:
        if not payload.items:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_TEMPLATE_ITEMS_REQUIRED",
                message="Checklist template harus memiliki minimal satu item.",
                status_code=422,
            )
        if payload.effective_to is not None and payload.effective_to < payload.effective_from:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_TEMPLATE_PERIOD_INVALID",
                message="effective_to tidak boleh lebih kecil dari effective_from.",
                status_code=422,
            )
        template = MaintenanceChecklistTemplate(
            template_code=payload.template_code,
            template_name=payload.template_name,
            asset_category_id=payload.asset_category_id,
            maintenance_type=(
                payload.maintenance_type.value if payload.maintenance_type is not None else None
            ),
            version_number=payload.version_number,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            is_active=payload.is_active,
        )
        try:
            await self.checklist_templates.create(template)
            for item_payload in payload.items:
                await self.checklist_template_items.create(
                    MaintenanceChecklistTemplateItem(
                        checklist_template_id=template.id,
                        sequence_no=item_payload.sequence_no,
                        item_code=item_payload.item_code,
                        instruction=item_payload.instruction,
                        response_type=item_payload.response_type.value,
                        is_required=item_payload.is_required,
                        normal_min_value=item_payload.normal_min_value,
                        normal_max_value=item_payload.normal_max_value,
                        unit_of_measure=item_payload.unit_of_measure,
                        failure_response_rule=(
                            item_payload.failure_response_rule.value
                            if item_payload.failure_response_rule is not None
                            else None
                        ),
                    )
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_CHECKLIST_TEMPLATE_CONFLICT",
                message="Checklist template atau sequence item menimbulkan konflik.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_checklist_template(template.id)

    async def get_checklist_template(self, template_id) -> MaintenanceChecklistTemplate:
        item = await self.checklist_templates.get(template_id)
        if item is None:
            raise MaintenanceChecklistTemplateNotFoundError(str(template_id))
        return item

    async def start_work_order_checklist(
        self,
        work_order_id,
        payload: MaintenanceChecklistExecutionStartPayload,
    ) -> MaintenanceChecklistExecution:
        work_order = await self.get_work_order(work_order_id)
        if work_order.status not in {
            MaintenanceWorkOrderStatus.APPROVED.value,
            MaintenanceWorkOrderStatus.ASSIGNED.value,
            MaintenanceWorkOrderStatus.IN_PROGRESS.value,
            MaintenanceWorkOrderStatus.COMPLETED.value,
        }:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_EXECUTION_INVALID_STATUS",
                message="Work order belum berada pada status yang mengizinkan checklist.",
                status_code=409,
            )
        checklist_template_id = payload.checklist_template_id
        if checklist_template_id is None and work_order.maintenance_plan_id is not None:
            plan = await self.get_plan(work_order.maintenance_plan_id)
            checklist_template_id = plan.checklist_template_id
        if checklist_template_id is None:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_TEMPLATE_REQUIRED",
                message="Checklist template wajib ditentukan untuk memulai checklist.",
                status_code=422,
            )
        template = await self.get_checklist_template(checklist_template_id)
        if not template.items:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_TEMPLATE_ITEMS_REQUIRED",
                message="Checklist template belum memiliki item.",
                status_code=422,
            )
        execution = MaintenanceChecklistExecution(
            checklist_template_id=template.id,
            work_order_id=work_order.id,
            maintenance_schedule_id=None,
            asset_id=work_order.asset_id,
            performed_by_employee_id=payload.performed_by_employee_id,
            started_at=payload.started_at,
            status=ChecklistExecutionStatus.IN_PROGRESS.value,
        )
        try:
            await self.checklist_executions.create(execution)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_checklist_execution(execution.id)

    async def get_checklist_execution(self, checklist_id) -> MaintenanceChecklistExecution:
        item = await self.checklist_executions.get(checklist_id)
        if item is None:
            raise MaintenanceChecklistExecutionNotFoundError(str(checklist_id))
        return item

    async def submit_checklist_results(
        self,
        checklist_id,
        payload: MaintenanceChecklistResultSubmitPayload,
    ) -> MaintenanceChecklistExecution:
        execution = await self.get_checklist_execution(checklist_id)
        if execution.status != ChecklistExecutionStatus.IN_PROGRESS.value:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_EXECUTION_INVALID_STATUS",
                message="Checklist execution harus IN_PROGRESS untuk menyimpan hasil.",
                status_code=409,
            )
        if execution.work_order_id is not None:
            work_order = await self.get_work_order(execution.work_order_id)
            if work_order.status == MaintenanceWorkOrderStatus.CLOSED.value:
                raise AppError(
                    code="MAINTENANCE_CHECKLIST_EXECUTION_INVALID_STATUS",
                    message="Checklist tidak dapat diubah setelah work order ditutup.",
                    status_code=409,
                )
        template_items = {item.id: item for item in execution.template.items}
        submitted_item_ids = {item.template_item_id for item in payload.results}
        required_item_ids = {
            item.id for item in execution.template.items if item.is_required is True
        }
        missing_required_ids = required_item_ids - submitted_item_ids
        if missing_required_ids:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_RESULT_REQUIRED",
                message="Masih ada item checklist wajib yang belum diisi.",
                status_code=422,
                details={
                    "missing_template_item_ids": [
                        str(item_id) for item_id in missing_required_ids
                    ]
                },
            )

        has_abnormal = False
        try:
            for index, entry in enumerate(payload.results, start=1):
                template_item = template_items.get(entry.template_item_id)
                if template_item is None:
                    raise AppError(
                        code="MAINTENANCE_CHECKLIST_RESULT_INVALID",
                        message="Template item tidak termasuk dalam checklist execution.",
                        status_code=422,
                    )
                self._validate_checklist_result_entry(template_item, entry)
                result_status, is_abnormal = self._derive_result_status(template_item, entry)
                has_abnormal = has_abnormal or is_abnormal
                result = await self.checklist_results.create(
                    MaintenanceChecklistResult(
                        checklist_execution_id=execution.id,
                        template_item_id=template_item.id,
                        result_status=result_status,
                        boolean_value=entry.boolean_value,
                        numeric_value=entry.numeric_value,
                        text_value=entry.text_value,
                        meter_reading_id=entry.meter_reading_id,
                        notes=entry.notes,
                        performed_at=entry.performed_at,
                    )
                )
                if is_abnormal:
                    created_finding = await self.findings.create(
                        MaintenanceFinding(
                            finding_number=self._generate_finding_number(
                                execution.id,
                                index,
                            ),
                            checklist_result_id=result.id,
                            work_order_id=execution.work_order_id,
                            asset_id=execution.asset_id,
                            finding_type=(
                                entry.finding_type.value
                                if entry.finding_type is not None
                                else MaintenanceFindingType.ABNORMAL_CONDITION.value
                            ),
                            severity=(
                                entry.finding_severity.value
                                if entry.finding_severity is not None
                                else MaintenanceFindingSeverity.MEDIUM.value
                            ),
                            description=(
                                entry.finding_description
                                or f"Hasil abnormal pada item {template_item.item_code}."
                            ),
                            recommended_action=entry.recommended_action,
                            requires_follow_up=(
                                entry.requires_follow_up
                                or template_item.failure_response_rule
                                == ChecklistFailureResponseRule.REQUIRES_FOLLOW_UP.value
                            ),
                            requires_asset_shutdown=(
                                entry.requires_asset_shutdown
                                or template_item.failure_response_rule
                                == ChecklistFailureResponseRule.REQUIRES_ASSET_SHUTDOWN.value
                            ),
                            follow_up_due_date=entry.follow_up_due_date,
                            status=MaintenanceFindingStatus.OPEN.value,
                            reported_by_employee_id=execution.performed_by_employee_id,
                            reported_at=entry.performed_at,
                        )
                    )
                    if execution.work_order_id is not None:
                        await self._record_work_order_event(
                            work_order_id=execution.work_order_id,
                            event_type=MaintenanceWorkOrderEventType.FINDING_CREATED.value,
                            previous_status=None,
                            new_status=None,
                            event_at=entry.performed_at,
                            performed_by=execution.performed_by_employee_id,
                            employee_id=execution.performed_by_employee_id,
                            reason=created_finding.description,
                            event_payload={"finding_id": str(created_finding.id)},
                        )

            await self.checklist_executions.update(
                execution,
                completed_at=payload.completed_at,
                overall_result=(
                    ChecklistOverallResult.FAIL.value
                    if has_abnormal
                    else ChecklistOverallResult.PASS.value
                ),
                status=ChecklistExecutionStatus.COMPLETED.value,
            )
            if execution.work_order_id is not None:
                await self._record_work_order_event(
                    work_order_id=execution.work_order_id,
                    event_type=MaintenanceWorkOrderEventType.CHECKLIST_COMPLETED.value,
                    previous_status=None,
                    new_status=None,
                    event_at=payload.completed_at,
                    performed_by=execution.performed_by_employee_id,
                    employee_id=execution.performed_by_employee_id,
                    reason="Checklist execution selesai.",
                    event_payload={"checklist_execution_id": str(execution.id)},
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_CHECKLIST_EXECUTION_CONFLICT",
                message="Checklist result atau finding menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_checklist_execution(checklist_id)

    async def get_finding(self, finding_id) -> MaintenanceFinding:
        item = await self.findings.get(finding_id)
        if item is None:
            raise MaintenanceFindingNotFoundError(str(finding_id))
        return item

    async def create_request_from_finding(
        self,
        finding_id,
        payload: MaintenanceFindingCreateRequestPayload,
    ) -> MaintenanceRequest:
        finding = await self.get_finding(finding_id)
        if finding.generated_request_id is not None:
            raise AppError(
                code="MAINTENANCE_FINDING_REQUEST_CONFLICT",
                message="Finding sudah memiliki follow-up request.",
                status_code=409,
            )
        await self._get_priority_or_raise(payload.priority_id)
        if payload.requested_vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.requested_vendor_partner_id)
        parent_request_id = None
        if finding.work_order is not None and getattr(finding.work_order, "requests", None):
            parent_request_id = finding.work_order.requests[0].maintenance_request_id
        request_item = MaintenanceRequest(
            request_number=payload.request_number,
            company_id=finding.asset.company_id,
            asset_id=finding.asset_id,
            parent_request_id=parent_request_id,
            request_type=MaintenanceRequestType.INSPECTION_FOLLOW_UP.value,
            source_type=MaintenanceRequestSourceType.CHECKLIST_FINDING.value,
            requested_by_employee_id=finding.reported_by_employee_id,
            reported_by_name=None,
            reported_at=payload.reported_at,
            title=payload.title,
            problem_description=payload.problem_description,
            priority_id=payload.priority_id,
            asset_location_id=finding.asset.current_location_id,
            operating_condition=None,
            is_asset_stopped=finding.requires_asset_shutdown,
            downtime_started_at=None,
            safety_impact=finding.finding_type == MaintenanceFindingType.SAFETY_RISK.value,
            environmental_impact=False,
            production_impact=finding.requires_asset_shutdown,
            maintenance_contract_id=None,
            warranty_id=None,
            requested_vendor_partner_id=payload.requested_vendor_partner_id,
            status=(
                MaintenanceRequestStatus.SUBMITTED.value
                if payload.submit
                else MaintenanceRequestStatus.DRAFT.value
            ),
            required_response_at=payload.required_response_at,
            required_resolution_at=payload.required_resolution_at,
            created_by=payload.created_by,
            updated_by=payload.updated_by or payload.created_by,
        )
        try:
            await self.requests.create(request_item)
            await self.findings.update(
                finding,
                generated_request_id=request_item.id,
                status=MaintenanceFindingStatus.FOLLOW_UP_CREATED.value,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_FINDING_REQUEST_CONFLICT",
                message="Follow-up request dari finding menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_request(request_item.id)

    async def create_failure(
        self,
        work_order_id: UUID,
        payload: AssetFailureCreate,
    ) -> MaintenanceWorkOrder:
        work_order = await self.get_work_order(work_order_id)
        if payload.failure_started_at is not None and payload.failure_ended_at is not None:
            if payload.failure_ended_at < payload.failure_started_at:
                raise AppError(
                    code="MAINTENANCE_ASSET_FAILURE_TIME_INVALID",
                    message="failure_ended_at tidak boleh lebih kecil dari failure_started_at.",
                    status_code=422,
                )
        if payload.failure_mode_id is not None:
            await self._get_failure_mode_or_raise(payload.failure_mode_id)
        if payload.symptom_code_id is not None:
            await self._get_symptom_code_or_raise(payload.symptom_code_id)
        if payload.root_cause_code_id is not None:
            await self._get_root_cause_code_or_raise(payload.root_cause_code_id)

        downtime_minutes = payload.downtime_minutes
        if (
            downtime_minutes is None
            and payload.failure_started_at is not None
            and payload.failure_ended_at is not None
        ):
            downtime_minutes = int(
                (payload.failure_ended_at - payload.failure_started_at).total_seconds() // 60
            )
        created_timestamp = datetime.now(UTC)

        failure = AssetFailure(
            failure_number=payload.failure_number,
            asset_id=work_order.asset_id,
            maintenance_request_id=(
                work_order.requests[0].maintenance_request_id if work_order.requests else None
            ),
            work_order_id=work_order.id,
            detected_at=payload.detected_at,
            detected_by_employee_id=payload.detected_by_employee_id,
            failure_mode_id=payload.failure_mode_id,
            symptom_code_id=payload.symptom_code_id,
            failure_description=payload.failure_description,
            failure_severity=payload.failure_severity.value,
            asset_condition_before=payload.asset_condition_before,
            asset_condition_after=payload.asset_condition_after,
            caused_shutdown=payload.caused_shutdown,
            safety_incident=payload.safety_incident,
            repeat_failure=payload.repeat_failure,
            temporary_action=payload.temporary_action,
            root_cause_code_id=payload.root_cause_code_id,
            root_cause_description=payload.root_cause_description,
            corrective_action=payload.corrective_action,
            preventive_action=payload.preventive_action,
            failure_started_at=payload.failure_started_at,
            failure_ended_at=payload.failure_ended_at,
            downtime_minutes=downtime_minutes,
            status=payload.status.value,
            created_at=created_timestamp,
            updated_at=created_timestamp,
            created_by=payload.created_by,
        )
        try:
            await self.failures.create(failure)
            await self._record_work_order_event(
                work_order_id=work_order.id,
                event_type=MaintenanceWorkOrderEventType.FAILURE_RECORDED.value,
                previous_status=None,
                new_status=work_order.status,
                event_at=payload.detected_at,
                performed_by=payload.created_by,
                employee_id=payload.detected_by_employee_id,
                reason=payload.failure_description,
                event_payload={
                    "failure_number": payload.failure_number,
                    "failure_severity": payload.failure_severity.value,
                    "status": payload.status.value,
                    "repeat_failure": payload.repeat_failure,
                    "caused_shutdown": payload.caused_shutdown,
                    "downtime_minutes": downtime_minutes,
                },
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_ASSET_FAILURE_CONFLICT",
                message="Asset failure menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def update_failure(
        self,
        failure_id: UUID,
        payload: AssetFailureUpdate,
        *,
        actor_id: UUID,
    ) -> AssetFailure:
        failure = await self.get_failure(failure_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return failure

        if "failure_mode_id" in changes and changes["failure_mode_id"] is not None:
            await self._get_failure_mode_or_raise(changes["failure_mode_id"])
        if "symptom_code_id" in changes and changes["symptom_code_id"] is not None:
            await self._get_symptom_code_or_raise(changes["symptom_code_id"])
        if "root_cause_code_id" in changes and changes["root_cause_code_id"] is not None:
            await self._get_root_cause_code_or_raise(changes["root_cause_code_id"])

        started_at = changes.get("failure_started_at", failure.failure_started_at)
        ended_at = changes.get("failure_ended_at", failure.failure_ended_at)
        if started_at is not None and ended_at is not None and ended_at < started_at:
            raise AppError(
                code="MAINTENANCE_ASSET_FAILURE_TIME_INVALID",
                message="failure_ended_at tidak boleh lebih kecil dari failure_started_at.",
                status_code=422,
            )

        if (
            "downtime_minutes" not in changes
            and started_at is not None
            and ended_at is not None
            and (
                "failure_started_at" in changes
                or "failure_ended_at" in changes
                or failure.downtime_minutes is None
            )
        ):
            changes["downtime_minutes"] = int((ended_at - started_at).total_seconds() // 60)

        if "failure_severity" in changes and changes["failure_severity"] is not None:
            changes["failure_severity"] = changes["failure_severity"].value
        if "status" in changes and changes["status"] is not None:
            changes["status"] = changes["status"].value

        previous_status = failure.status
        next_status = changes.get("status", failure.status)
        changes["updated_at"] = datetime.now(UTC)
        rca_finalized = (
            (
                "root_cause_code_id" in changes and changes["root_cause_code_id"] is not None
            )
            or (
                "root_cause_description" in changes
                and bool(changes["root_cause_description"])
            )
            or ("corrective_action" in changes and bool(changes["corrective_action"]))
            or ("preventive_action" in changes and bool(changes["preventive_action"]))
        )

        try:
            await self.failures.update(failure, **changes)
            if failure.work_order_id is not None:
                await self._record_work_order_event(
                    work_order_id=failure.work_order_id,
                    event_type=(
                        MaintenanceWorkOrderEventType.RCA_FINALIZED.value
                        if rca_finalized
                        else MaintenanceWorkOrderEventType.FAILURE_UPDATED.value
                    ),
                    previous_status=previous_status,
                    new_status=next_status,
                    event_at=changes.get("detected_at", datetime.now(UTC)),
                    performed_by=actor_id,
                    employee_id=changes.get(
                        "detected_by_employee_id",
                        failure.detected_by_employee_id,
                    ),
                    reason=changes.get("root_cause_description")
                    or changes.get("corrective_action")
                    or changes.get("failure_description"),
                    event_payload={
                        "failure_id": str(failure.id),
                        "failure_number": failure.failure_number,
                        "status": next_status,
                        "root_cause_code_id": (
                            str(changes["root_cause_code_id"])
                            if changes.get("root_cause_code_id") is not None
                            else None
                        ),
                        "repeat_failure": changes.get("repeat_failure", failure.repeat_failure),
                        "caused_shutdown": changes.get(
                            "caused_shutdown",
                            failure.caused_shutdown,
                        ),
                        "downtime_minutes": changes.get(
                            "downtime_minutes",
                            failure.downtime_minutes,
                        ),
                    },
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_ASSET_FAILURE_CONFLICT",
                message="Perubahan asset failure menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        return await self.get_failure(failure_id)

    async def get_failure(self, failure_id: UUID) -> AssetFailure:
        item = await self.failures.get(failure_id)
        if item is None:
            raise MaintenanceAssetFailureNotFoundError(str(failure_id))
        return item

    async def list_failures(
        self,
        pagination: PaginationParams,
        *,
        asset_id: UUID | None = None,
        work_order_id: UUID | None = None,
        status: str | None = None,
        failure_mode_id: UUID | None = None,
        root_cause_code_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[AssetFailure], int]:
        items, total_items = await self.failures.list(
            pagination,
            asset_id=asset_id,
            work_order_id=work_order_id,
            status=status,
            failure_mode_id=failure_mode_id,
            root_cause_code_id=root_cause_code_id,
            date_from=date_from,
            date_to=date_to,
        )
        return list(items), total_items

    async def create_downtime(
        self,
        work_order_id,
        payload: MaintenanceDowntimeCreate,
    ) -> MaintenanceWorkOrder:
        work_order = await self.get_work_order(work_order_id)
        if payload.ended_at is not None and payload.ended_at < payload.started_at:
            raise AppError(
                code="MAINTENANCE_DOWNTIME_TIME_INVALID",
                message="ended_at tidak boleh lebih kecil dari started_at.",
                status_code=422,
            )
        duration_minutes = payload.duration_minutes
        if duration_minutes is None and payload.ended_at is not None:
            duration_minutes = int((payload.ended_at - payload.started_at).total_seconds() // 60)
        downtime = MaintenanceDowntime(
            asset_id=work_order.asset_id,
            maintenance_request_id=(
                work_order.requests[0].maintenance_request_id if work_order.requests else None
            ),
            work_order_id=work_order.id,
            downtime_type=payload.downtime_type.value,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            duration_minutes=duration_minutes,
            production_loss_quantity=payload.production_loss_quantity,
            unit_of_measure=payload.unit_of_measure,
            reason=payload.reason,
        )
        try:
            await self.downtimes.create(downtime)
            await self._record_work_order_event(
                work_order_id=work_order.id,
                event_type=MaintenanceWorkOrderEventType.DOWNTIME_RECORDED.value,
                previous_status=None,
                new_status=work_order.status,
                event_at=payload.started_at,
                reason=payload.reason,
                event_payload={
                    "downtime_type": payload.downtime_type.value,
                    "duration_minutes": duration_minutes,
                },
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def list_work_order_events(self, work_order_id) -> list[MaintenanceWorkOrderEvent]:
        await self.get_work_order(work_order_id)
        return list(await self.events.list_by_work_order(work_order_id))

    async def list_downtimes(self, work_order_id) -> list[MaintenanceDowntime]:
        await self.get_work_order(work_order_id)
        return list(await self.downtimes.list_by_work_order(work_order_id))

    async def create_part_usage(
        self,
        work_order_id,
        payload: MaintenancePartUsageCreate,
    ) -> MaintenanceWorkOrder:
        work_order = await self.get_work_order(work_order_id)
        if work_order.status not in {
            MaintenanceWorkOrderStatus.APPROVED.value,
            MaintenanceWorkOrderStatus.ASSIGNED.value,
            MaintenanceWorkOrderStatus.IN_PROGRESS.value,
            MaintenanceWorkOrderStatus.COMPLETED.value,
            MaintenanceWorkOrderStatus.VERIFICATION.value,
        }:
            raise AppError(
                code="MAINTENANCE_PART_USAGE_INVALID_STATUS",
                message="Work order belum berada pada status yang mengizinkan part usage.",
                status_code=409,
            )
        part_usage = MaintenancePartUsage(
            work_order_id=work_order.id,
            part_item_id=payload.part_item_id,
            asset_id=work_order.asset_id,
            quantity=payload.quantity,
            unit_cost=payload.unit_cost,
            currency_code=payload.currency_code or work_order.currency_code,
            usage_type=payload.usage_type.value,
            used_at=payload.used_at,
            used_by_employee_id=payload.used_by_employee_id,
            sap_inventory_doc_entry=payload.sap_inventory_doc_entry,
            sap_inventory_doc_num=payload.sap_inventory_doc_num,
            removed_component_asset_id=payload.removed_component_asset_id,
            installed_component_asset_id=payload.installed_component_asset_id,
            serial_number=payload.serial_number,
        )
        try:
            await self.part_usages.create(part_usage)
            actual_part_cost = await self._calculate_actual_part_cost(work_order.id)
            await self.work_orders.update(
                work_order,
                actual_part_cost=actual_part_cost,
                updated_by=payload.used_by_employee_id or work_order.updated_by,
            )
            await self._record_work_order_event(
                work_order_id=work_order.id,
                event_type=MaintenanceWorkOrderEventType.PART_ISSUED.value,
                previous_status=None,
                new_status=work_order.status,
                event_at=payload.used_at,
                performed_by=payload.used_by_employee_id,
                employee_id=payload.used_by_employee_id,
                reason=None,
                event_payload={
                    "part_item_id": str(payload.part_item_id),
                    "quantity": str(payload.quantity),
                    "usage_type": payload.usage_type.value,
                },
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_PART_USAGE_CONFLICT",
                message="Part usage menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def create_labor_log(
        self,
        work_order_id,
        payload: MaintenanceLaborLogCreate,
    ) -> MaintenanceWorkOrder:
        work_order = await self.get_work_order(work_order_id)
        if work_order.status not in {
            MaintenanceWorkOrderStatus.APPROVED.value,
            MaintenanceWorkOrderStatus.ASSIGNED.value,
            MaintenanceWorkOrderStatus.IN_PROGRESS.value,
            MaintenanceWorkOrderStatus.COMPLETED.value,
            MaintenanceWorkOrderStatus.VERIFICATION.value,
        }:
            raise AppError(
                code="MAINTENANCE_LABOR_LOG_INVALID_STATUS",
                message="Work order belum berada pada status yang mengizinkan labor log.",
                status_code=409,
            )
        if payload.ended_at is not None and payload.ended_at < payload.started_at:
            raise AppError(
                code="MAINTENANCE_LABOR_LOG_TIME_INVALID",
                message="ended_at tidak boleh lebih kecil dari started_at.",
                status_code=422,
            )
        duration_minutes = payload.duration_minutes
        if duration_minutes is None and payload.ended_at is not None:
            duration_minutes = int((payload.ended_at - payload.started_at).total_seconds() // 60)
        labor_cost = payload.labor_cost
        if labor_cost is None and payload.hourly_rate is not None and duration_minutes is not None:
            labor_cost = (Decimal(duration_minutes) / Decimal("60")) * payload.hourly_rate
        labor_log = MaintenanceLaborLog(
            work_order_id=work_order.id,
            employee_id=payload.employee_id,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            duration_minutes=duration_minutes,
            activity_type=payload.activity_type.value,
            hourly_rate=payload.hourly_rate,
            labor_cost=labor_cost,
            notes=payload.notes,
        )
        try:
            await self.labor_logs.create(labor_log)
            actual_labor_cost = await self._calculate_actual_labor_cost(work_order.id)
            await self.work_orders.update(
                work_order,
                actual_labor_cost=actual_labor_cost,
                updated_by=payload.employee_id,
            )
            await self._record_work_order_event(
                work_order_id=work_order.id,
                event_type=MaintenanceWorkOrderEventType.LABOR_LOGGED.value,
                previous_status=None,
                new_status=work_order.status,
                event_at=payload.ended_at or payload.started_at,
                performed_by=payload.employee_id,
                employee_id=payload.employee_id,
                reason=payload.notes,
                event_payload={
                    "activity_type": payload.activity_type.value,
                    "duration_minutes": duration_minutes,
                    "labor_cost": str(labor_cost) if labor_cost is not None else None,
                },
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_LABOR_LOG_CONFLICT",
                message="Labor log menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def create_request(self, payload: MaintenanceRequestCreate) -> MaintenanceRequest:
        asset = await self._get_asset_or_raise(payload.asset_id)
        priority = await self._get_priority_or_raise(payload.priority_id)
        if payload.parent_request_id is not None:
            await self.get_request(payload.parent_request_id)
        if payload.asset_location_id is not None:
            await self._get_location_or_raise(payload.asset_location_id)
        if payload.requested_vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.requested_vendor_partner_id)

        item = MaintenanceRequest(
            request_number=payload.request_number,
            company_id=payload.company_id,
            asset_id=asset.id,
            parent_request_id=payload.parent_request_id,
            request_type=payload.request_type.value,
            source_type=payload.source_type.value,
            requested_by_employee_id=payload.requested_by_employee_id,
            reported_by_name=payload.reported_by_name,
            reported_at=payload.reported_at,
            title=payload.title,
            problem_description=payload.problem_description,
            priority_id=priority.id,
            asset_location_id=payload.asset_location_id,
            operating_condition=payload.operating_condition,
            is_asset_stopped=payload.is_asset_stopped,
            downtime_started_at=payload.downtime_started_at,
            safety_impact=payload.safety_impact,
            environmental_impact=payload.environmental_impact,
            production_impact=payload.production_impact,
            maintenance_contract_id=payload.maintenance_contract_id,
            warranty_id=payload.warranty_id,
            requested_vendor_partner_id=payload.requested_vendor_partner_id,
            status=MaintenanceRequestStatus.DRAFT.value,
            required_response_at=payload.required_response_at,
            required_resolution_at=payload.required_resolution_at,
            created_by=payload.created_by,
            updated_by=payload.updated_by or payload.created_by,
        )
        try:
            await self.requests.create(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_REQUEST_CONFLICT",
                message="Request number maintenance sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_request(item.id)

    async def list_requests(
        self,
        pagination: PaginationParams,
    ) -> tuple[list[MaintenanceRequest], int]:
        items, total_items = await self.requests.list(pagination)
        return list(items), total_items

    async def get_request(self, request_id):
        item = await self.requests.get(request_id)
        if item is None:
            raise MaintenanceRequestNotFoundError(str(request_id))
        return item

    async def submit_request(
        self,
        request_id,
        payload: MaintenanceRequestActionPayload,
    ) -> MaintenanceRequest:
        item = await self.get_request(request_id)
        if item.status != MaintenanceRequestStatus.DRAFT.value:
            raise AppError(
                code="MAINTENANCE_REQUEST_INVALID_STATUS",
                message="Hanya request DRAFT yang dapat disubmit.",
                status_code=409,
            )
        try:
            await self.requests.update(
                item,
                status=MaintenanceRequestStatus.SUBMITTED.value,
                updated_by=payload.actor_id,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_request(request_id)

    async def triage_request(
        self,
        request_id,
        payload: MaintenanceRequestTriagePayload,
    ) -> MaintenanceRequest:
        item = await self.get_request(request_id)
        if item.status not in {
            MaintenanceRequestStatus.SUBMITTED.value,
            MaintenanceRequestStatus.WAITING_INFORMATION.value,
        }:
            raise AppError(
                code="MAINTENANCE_REQUEST_INVALID_STATUS",
                message="Request harus SUBMITTED atau WAITING_INFORMATION untuk ditriage.",
                status_code=409,
            )
        changes: dict[str, object] = {
            "status": MaintenanceRequestStatus.TRIAGE.value,
            "triaged_by_employee_id": payload.actor_id,
            "triaged_at": payload.acted_at,
            "updated_by": payload.actor_id,
        }
        if payload.priority_id is not None:
            priority = await self._get_priority_or_raise(payload.priority_id)
            changes["priority_id"] = priority.id
        if payload.asset_location_id is not None:
            await self._get_location_or_raise(payload.asset_location_id)
            changes["asset_location_id"] = payload.asset_location_id
        if payload.requested_vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.requested_vendor_partner_id)
            changes["requested_vendor_partner_id"] = payload.requested_vendor_partner_id
        if payload.operating_condition is not None:
            changes["operating_condition"] = payload.operating_condition
        if payload.required_response_at is not None:
            changes["required_response_at"] = payload.required_response_at
        if payload.required_resolution_at is not None:
            changes["required_resolution_at"] = payload.required_resolution_at
        try:
            await self.requests.update(item, **changes)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_request(request_id)

    async def approve_request(
        self,
        request_id,
        payload: MaintenanceRequestActionPayload,
    ) -> MaintenanceRequest:
        item = await self.get_request(request_id)
        if item.status != MaintenanceRequestStatus.TRIAGE.value:
            raise AppError(
                code="MAINTENANCE_REQUEST_INVALID_STATUS",
                message="Hanya request TRIAGE yang dapat diapprove.",
                status_code=409,
            )
        try:
            await self.requests.update(
                item,
                status=MaintenanceRequestStatus.APPROVED.value,
                updated_by=payload.actor_id,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_request(request_id)

    async def reject_request(
        self,
        request_id,
        payload: MaintenanceRequestRejectPayload,
    ) -> MaintenanceRequest:
        item = await self.get_request(request_id)
        if item.status not in {
            MaintenanceRequestStatus.SUBMITTED.value,
            MaintenanceRequestStatus.TRIAGE.value,
        }:
            raise AppError(
                code="MAINTENANCE_REQUEST_INVALID_STATUS",
                message="Hanya request SUBMITTED atau TRIAGE yang dapat direject.",
                status_code=409,
            )
        try:
            await self.requests.update(
                item,
                status=MaintenanceRequestStatus.REJECTED.value,
                rejection_reason=payload.rejection_reason,
                updated_by=payload.actor_id,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_request(request_id)

    async def convert_request_to_work_order(
        self,
        request_id,
        payload: MaintenanceConvertToWorkOrderPayload,
    ) -> MaintenanceWorkOrder:
        request = await self.get_request(request_id)
        if request.status != MaintenanceRequestStatus.APPROVED.value:
            raise AppError(
                code="MAINTENANCE_REQUEST_INVALID_STATUS",
                message="Request harus APPROVED sebelum dikonversi menjadi work order.",
                status_code=409,
            )
        asset = await self._get_asset_or_raise(request.asset_id)
        priority = await self._get_priority_or_raise(request.priority_id)
        if payload.vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.vendor_partner_id)
        work_order = MaintenanceWorkOrder(
            work_order_number=payload.work_order_number,
            company_id=request.company_id,
            asset_id=asset.id,
            maintenance_type=payload.maintenance_type.value,
            priority_id=priority.id,
            title=request.title,
            scope_of_work=payload.scope_of_work,
            execution_mode=payload.execution_mode.value,
            vendor_partner_id=payload.vendor_partner_id,
            planned_start_at=payload.planned_start_at,
            planned_end_at=payload.planned_end_at,
            asset_condition_before=asset.condition_status,
            requires_shutdown=payload.requires_shutdown,
            requires_permit=payload.requires_permit,
            requires_verification=payload.requires_verification,
            status=MaintenanceWorkOrderStatus.WAITING_APPROVAL.value,
            created_by=payload.created_by,
            updated_by=payload.updated_by or payload.created_by,
        )
        link = MaintenanceRequestWorkOrder(
            maintenance_request_id=request.id,
            work_order_id=work_order.id,
            relationship_type=payload.relationship_type.value,
        )
        try:
            created = await self.work_orders.create(work_order)
            link.work_order_id = created.id
            await self.request_work_orders.create(link)
            await self.requests.update(
                request,
                status=MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER.value,
                updated_by=payload.created_by,
            )
            await self._record_work_order_event(
                work_order_id=created.id,
                event_type=MaintenanceWorkOrderEventType.CREATED.value,
                previous_status=None,
                new_status=work_order.status,
                event_at=request.reported_at,
                performed_by=payload.created_by,
                reason="Work order dibuat dari maintenance request.",
                event_payload={"request_id": str(request.id)},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CONFLICT",
                message="Work order number sudah digunakan atau terjadi konflik konversi.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order.id)

    async def create_work_order(self, payload: MaintenanceWorkOrderCreate) -> MaintenanceWorkOrder:
        await self._get_asset_or_raise(payload.asset_id)
        await self._get_priority_or_raise(payload.priority_id)
        if payload.vendor_partner_id is not None:
            await self._get_partner_or_raise(payload.vendor_partner_id)
        item = MaintenanceWorkOrder(
            work_order_number=payload.work_order_number,
            company_id=payload.company_id,
            asset_id=payload.asset_id,
            maintenance_type=payload.maintenance_type.value,
            priority_id=payload.priority_id,
            title=payload.title,
            scope_of_work=payload.scope_of_work,
            execution_mode=payload.execution_mode.value,
            vendor_partner_id=payload.vendor_partner_id,
            planned_start_at=payload.planned_start_at,
            planned_end_at=payload.planned_end_at,
            asset_condition_before=payload.asset_condition_before,
            requires_shutdown=payload.requires_shutdown,
            requires_permit=payload.requires_permit,
            requires_verification=payload.requires_verification,
            status=MaintenanceWorkOrderStatus.WAITING_APPROVAL.value,
            estimated_labor_cost=payload.estimated_labor_cost,
            estimated_part_cost=payload.estimated_part_cost,
            estimated_vendor_cost=payload.estimated_vendor_cost,
            currency_code=payload.currency_code,
            created_by=payload.created_by,
            updated_by=payload.updated_by or payload.created_by,
        )
        try:
            await self.work_orders.create(item)
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.CREATED.value,
                previous_status=None,
                new_status=item.status,
                event_at=datetime.now(UTC),
                performed_by=payload.created_by,
                reason="Work order dibuat manual.",
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CONFLICT",
                message="Work order number sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(item.id)

    async def list_work_orders(
        self,
        pagination: PaginationParams,
    ) -> tuple[list[MaintenanceWorkOrder], int]:
        items, total_items = await self.work_orders.list(pagination)
        return list(items), total_items

    async def get_work_order(self, work_order_id):
        item = await self.work_orders.get(work_order_id)
        if item is None:
            raise MaintenanceWorkOrderNotFoundError(str(work_order_id))
        return item

    async def approve_work_order(
        self,
        work_order_id,
        payload: MaintenanceRequestActionPayload,
    ) -> MaintenanceWorkOrder:
        item = await self.get_work_order(work_order_id)
        if item.status not in {
            MaintenanceWorkOrderStatus.DRAFT.value,
            MaintenanceWorkOrderStatus.WAITING_APPROVAL.value,
        }:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_INVALID_STATUS",
                message="Work order harus DRAFT atau WAITING_APPROVAL untuk diapprove.",
                status_code=409,
            )
        try:
            previous_status = item.status
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.APPROVED.value,
                approved_by=payload.actor_id,
                approved_at=payload.acted_at,
                updated_by=payload.actor_id,
            )
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.APPROVED.value,
                previous_status=previous_status,
                new_status=MaintenanceWorkOrderStatus.APPROVED.value,
                event_at=payload.acted_at,
                performed_by=payload.actor_id,
                reason=payload.notes,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def assign_work_order(
        self,
        work_order_id,
        payload: MaintenanceWorkOrderAssignPayload,
    ) -> MaintenanceWorkOrder:
        item = await self.get_work_order(work_order_id)
        if item.status not in {
            MaintenanceWorkOrderStatus.APPROVED.value,
            MaintenanceWorkOrderStatus.PLANNED.value,
            MaintenanceWorkOrderStatus.ASSIGNED.value,
        }:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_INVALID_STATUS",
                message="Work order belum siap untuk assignment.",
                status_code=409,
            )
        assignment = MaintenanceWorkOrderAssignment(
            work_order_id=item.id,
            employee_id=payload.employee_id,
            assignment_role=payload.assignment_role.value,
            planned_minutes=payload.planned_minutes,
            assigned_at=payload.acted_at,
            accepted_at=payload.accepted_at,
        )
        try:
            previous_status = item.status
            await self.assignments.create(assignment)
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.ASSIGNED.value,
                lead_technician_id=payload.employee_id
                if payload.assignment_role.value == "LEAD_TECHNICIAN"
                else item.lead_technician_id,
                updated_by=payload.actor_id,
            )
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.ASSIGNED.value,
                previous_status=previous_status,
                new_status=MaintenanceWorkOrderStatus.ASSIGNED.value,
                event_at=payload.acted_at,
                performed_by=payload.actor_id,
                employee_id=payload.employee_id,
                event_payload={"assignment_role": payload.assignment_role.value},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_ASSIGNMENT_CONFLICT",
                message="Assignment teknisi work order sudah ada.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def start_work_order(
        self,
        work_order_id,
        payload: MaintenanceRequestActionPayload,
    ) -> MaintenanceWorkOrder:
        item = await self.get_work_order(work_order_id)
        if item.status not in {
            MaintenanceWorkOrderStatus.APPROVED.value,
            MaintenanceWorkOrderStatus.ASSIGNED.value,
        }:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_INVALID_STATUS",
                message="Work order harus APPROVED atau ASSIGNED untuk dimulai.",
                status_code=409,
            )
        asset = await self._get_asset_or_raise(item.asset_id)
        try:
            previous_status = item.status
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
                actual_start_at=payload.acted_at,
                updated_by=payload.actor_id,
            )
            await self.asset_status_histories.create(
                AssetStatusHistory(
                    asset_id=asset.id,
                    previous_status=asset.asset_status,
                    new_status=AssetStatus.UNDER_MAINTENANCE.value,
                    previous_condition=asset.condition_status,
                    new_condition=asset.condition_status,
                    effective_at=payload.acted_at,
                    reason=f"Work order {item.work_order_number} dimulai.",
                    reference_type="MAINTENANCE_WORK_ORDER",
                    reference_id=item.id,
                    changed_by=payload.actor_id,
                )
            )
            await self.assets.update(
                asset,
                asset_status=AssetStatus.UNDER_MAINTENANCE.value,
                updated_by=payload.actor_id,
            )
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.STARTED.value,
                previous_status=previous_status,
                new_status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
                event_at=payload.acted_at,
                performed_by=payload.actor_id,
                reason=payload.notes,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def complete_work_order(
        self,
        work_order_id,
        payload: MaintenanceWorkOrderCompletePayload,
    ) -> MaintenanceWorkOrder:
        item = await self.get_work_order(work_order_id)
        if item.status != MaintenanceWorkOrderStatus.IN_PROGRESS.value:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_INVALID_STATUS",
                message="Hanya work order IN_PROGRESS yang dapat diselesaikan.",
                status_code=409,
            )
        if payload.acted_at < item.actual_start_at:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_TIME_INVALID",
                message="actual_end_at tidak boleh lebih kecil dari actual_start_at.",
                status_code=422,
            )
        try:
            previous_status = item.status
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.COMPLETED.value,
                actual_end_at=payload.acted_at,
                completion_summary=payload.completion_summary,
                asset_condition_after=payload.asset_condition_after,
                resolution_code=payload.resolution_code,
                actual_labor_cost=payload.actual_labor_cost,
                actual_part_cost=payload.actual_part_cost,
                actual_vendor_cost=payload.actual_vendor_cost,
                updated_by=payload.actor_id,
            )
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.COMPLETED.value,
                previous_status=previous_status,
                new_status=MaintenanceWorkOrderStatus.COMPLETED.value,
                event_at=payload.acted_at,
                performed_by=payload.actor_id,
                reason=payload.completion_summary,
                event_payload={"resolution_code": payload.resolution_code},
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def verify_work_order(
        self,
        work_order_id,
        payload: MaintenanceWorkOrderVerifyPayload,
    ) -> MaintenanceWorkOrder:
        item = await self.get_work_order(work_order_id)
        if item.status != MaintenanceWorkOrderStatus.COMPLETED.value:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_INVALID_STATUS",
                message="Hanya work order COMPLETED yang dapat diverifikasi.",
                status_code=409,
            )
        try:
            previous_status = item.status
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.VERIFICATION.value,
                verified_by_employee_id=payload.actor_id,
                verified_at=payload.acted_at,
                updated_by=payload.actor_id,
            )
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.VERIFIED.value,
                previous_status=previous_status,
                new_status=MaintenanceWorkOrderStatus.VERIFICATION.value,
                event_at=payload.acted_at,
                performed_by=payload.actor_id,
                employee_id=payload.actor_id,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def close_work_order(
        self,
        work_order_id,
        payload: MaintenanceRequestActionPayload,
    ) -> MaintenanceWorkOrder:
        item = await self.get_work_order(work_order_id)
        valid_statuses = {MaintenanceWorkOrderStatus.COMPLETED.value}
        if item.requires_verification:
            valid_statuses = {MaintenanceWorkOrderStatus.VERIFICATION.value}
        if item.status not in valid_statuses:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_INVALID_STATUS",
                message="Work order belum memenuhi syarat untuk ditutup.",
                status_code=409,
            )
        if (
            item.actual_start_at is None
            or item.actual_end_at is None
            or not item.completion_summary
        ):
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CLOSE_REQUIREMENTS_INCOMPLETE",
                message="Work order belum memiliki data penyelesaian yang wajib.",
                status_code=422,
            )
        checklist_executions = await self.checklist_executions.list_by_work_order(item.id)
        incomplete_checklists = [
            checklist
            for checklist in checklist_executions
            if checklist.status != ChecklistExecutionStatus.COMPLETED.value
        ]
        if incomplete_checklists:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CLOSE_REQUIREMENTS_INCOMPLETE",
                message="Masih ada checklist work order yang belum selesai.",
                status_code=422,
            )
        findings = await self.findings.list_by_work_order(item.id)
        pending_follow_ups = [
            finding
            for finding in findings
            if finding.requires_follow_up
            and finding.status != MaintenanceFindingStatus.RESOLVED.value
            and finding.generated_request_id is None
        ]
        if pending_follow_ups:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CLOSE_REQUIREMENTS_INCOMPLETE",
                message="Masih ada finding yang membutuhkan follow-up request.",
                status_code=422,
            )
        asset = await self._get_asset_or_raise(item.asset_id)
        new_condition = item.asset_condition_after or asset.condition_status
        actual_part_cost = await self._calculate_actual_part_cost(item.id)
        actual_labor_cost = await self._calculate_actual_labor_cost(item.id)
        try:
            previous_status = item.status
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.CLOSED.value,
                closed_by=payload.actor_id,
                closed_at=payload.acted_at,
                actual_part_cost=actual_part_cost,
                actual_labor_cost=actual_labor_cost,
                updated_by=payload.actor_id,
            )
            await self.asset_status_histories.create(
                AssetStatusHistory(
                    asset_id=asset.id,
                    previous_status=asset.asset_status,
                    new_status=AssetStatus.IN_SERVICE.value,
                    previous_condition=asset.condition_status,
                    new_condition=new_condition,
                    effective_at=payload.acted_at,
                    reason=f"Work order {item.work_order_number} ditutup.",
                    reference_type="MAINTENANCE_WORK_ORDER",
                    reference_id=item.id,
                    changed_by=payload.actor_id,
                )
            )
            await self.assets.update(
                asset,
                asset_status=AssetStatus.IN_SERVICE.value,
                condition_status=(
                    new_condition
                    if new_condition in {member.value for member in ConditionStatus}
                    else asset.condition_status
                ),
                updated_by=payload.actor_id,
            )
            for link in item.requests:
                await self.requests.update(
                    link.request,
                    status=MaintenanceRequestStatus.CLOSED.value,
                    updated_by=payload.actor_id,
                )
            await self._record_work_order_event(
                work_order_id=item.id,
                event_type=MaintenanceWorkOrderEventType.CLOSED.value,
                previous_status=previous_status,
                new_status=MaintenanceWorkOrderStatus.CLOSED.value,
                event_at=payload.acted_at,
                performed_by=payload.actor_id,
                reason=payload.notes,
                event_payload={
                    "actual_part_cost": str(actual_part_cost),
                    "actual_labor_cost": str(actual_labor_cost),
                },
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return await self.get_work_order(work_order_id)

    async def get_asset_maintenance_history(
        self,
        asset_id,
    ) -> list[AssetMaintenanceHistoryItemRead]:
        await self._get_asset_or_raise(asset_id)
        items = await self.work_orders.list_by_asset(asset_id)
        return [AssetMaintenanceHistoryItemRead.from_model(item) for item in items]

    async def get_backlog_report(self) -> MaintenanceBacklogReportRead:
        generated_at = datetime.now(UTC)
        summary = await self.reports.get_backlog_summary(as_of=generated_at)
        return MaintenanceBacklogReportRead(generated_at=generated_at, **summary)

    async def get_cost_report(
        self,
        pagination: PaginationParams,
        *,
        asset_id: UUID | None = None,
        maintenance_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[MaintenanceCostReportItemRead], int]:
        items, total_items = await self.reports.list_cost_report(
            pagination,
            asset_id=asset_id,
            maintenance_type=maintenance_type,
            date_from=date_from,
            date_to=date_to,
        )
        return [MaintenanceCostReportItemRead.from_model(item) for item in items], total_items

    async def get_sla_report(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> MaintenanceSlaReportRead:
        generated_at = datetime.now(UTC)
        summary = await self.reports.get_sla_summary(
            as_of=generated_at,
            date_from=date_from,
            date_to=date_to,
        )
        response_target = summary["response_sla_target_count"]
        resolution_target = summary["resolution_sla_target_count"]
        response_pct = Decimal("0")
        resolution_pct = Decimal("0")
        if response_target > 0:
            response_pct = (
                Decimal(summary["response_sla_met_count"])
                * Decimal("100")
                / Decimal(response_target)
            ).quantize(Decimal("0.01"))
        if resolution_target > 0:
            resolution_pct = (
                Decimal(summary["resolution_sla_met_count"])
                * Decimal("100")
                / Decimal(resolution_target)
            ).quantize(Decimal("0.01"))
        return MaintenanceSlaReportRead(
            generated_at=generated_at,
            response_sla_target_count=response_target,
            response_sla_met_count=summary["response_sla_met_count"],
            response_sla_breached_count=summary["response_sla_breached_count"],
            response_sla_compliance_pct=response_pct,
            resolution_sla_target_count=resolution_target,
            resolution_sla_met_count=summary["resolution_sla_met_count"],
            resolution_sla_breached_count=summary["resolution_sla_breached_count"],
            resolution_sla_compliance_pct=resolution_pct,
        )

    async def get_reliability_report(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> MaintenanceReliabilityReportRead:
        generated_at = datetime.now(UTC)
        summary = await self.reports.get_reliability_summary(
            date_from=date_from,
            date_to=date_to,
        )
        completed_repair_count = int(summary["completed_repair_count"])
        unplanned_work_order_count = int(summary["unplanned_work_order_count"])
        planned_work_order_count = int(summary["planned_work_order_count"])
        total_repair_minutes = Decimal(str(summary["total_repair_minutes"]))
        total_downtime_minutes = int(summary["total_downtime_minutes"])
        downtime_count = int(summary["downtime_count"])

        mttr_minutes = Decimal("0")
        average_downtime_minutes = Decimal("0")
        planned_vs_unplanned_ratio = Decimal("0")
        if completed_repair_count > 0:
            mttr_minutes = (total_repair_minutes / Decimal(completed_repair_count)).quantize(
                Decimal("0.01")
            )
        if downtime_count > 0:
            average_downtime_minutes = (
                Decimal(total_downtime_minutes) / Decimal(downtime_count)
            ).quantize(Decimal("0.01"))
        if unplanned_work_order_count > 0:
            planned_vs_unplanned_ratio = (
                Decimal(planned_work_order_count) / Decimal(unplanned_work_order_count)
            ).quantize(Decimal("0.01"))

        return MaintenanceReliabilityReportRead(
            generated_at=generated_at,
            completed_repair_count=completed_repair_count,
            breakdown_work_order_count=int(summary["breakdown_work_order_count"]),
            preventive_work_order_count=int(summary["preventive_work_order_count"]),
            unplanned_work_order_count=unplanned_work_order_count,
            planned_work_order_count=planned_work_order_count,
            mttr_minutes=mttr_minutes,
            total_downtime_minutes=total_downtime_minutes,
            average_downtime_minutes=average_downtime_minutes,
            planned_vs_unplanned_ratio=planned_vs_unplanned_ratio,
            repeat_failure_asset_count=int(summary["repeat_failure_asset_count"]),
        )

    async def get_failure_analysis_report(
        self,
        *,
        asset_id: UUID | None = None,
        failure_mode_id: UUID | None = None,
        root_cause_code_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> MaintenanceFailureAnalysisReportRead:
        generated_at = datetime.now(UTC)
        summary = await self.reports.get_failure_analysis_summary(
            asset_id=asset_id,
            failure_mode_id=failure_mode_id,
            root_cause_code_id=root_cause_code_id,
            date_from=date_from,
            date_to=date_to,
        )
        failure_count = int(summary["failure_count"])
        open_failure_count = int(summary["open_failure_count"])
        under_analysis_count = int(summary["under_analysis_count"])
        resolved_failure_count = int(summary["resolved_failure_count"])
        closed_failure_count = int(summary["closed_failure_count"])
        repeat_failure_count = int(summary["repeat_failure_count"])
        rca_completed_count = int(summary["rca_completed_count"])
        rca_pending_count = int(summary["rca_pending_count"])
        total_downtime_minutes = int(summary["total_downtime_minutes"])
        caused_shutdown_count = int(summary["caused_shutdown_count"])
        safety_incident_count = int(summary["safety_incident_count"])
        intervals_in_hours = list(summary["intervals_in_hours"])

        repeat_failure_rate_pct = Decimal("0")
        rca_completion_rate_pct = Decimal("0")
        average_downtime_minutes = Decimal("0")
        mtbf_hours = Decimal("0")
        if failure_count > 0:
            repeat_failure_rate_pct = (
                Decimal(repeat_failure_count) * Decimal("100") / Decimal(failure_count)
            ).quantize(Decimal("0.01"))
            rca_completion_rate_pct = (
                Decimal(rca_completed_count) * Decimal("100") / Decimal(failure_count)
            ).quantize(Decimal("0.01"))
            average_downtime_minutes = (
                Decimal(total_downtime_minutes) / Decimal(failure_count)
            ).quantize(Decimal("0.01"))
        if intervals_in_hours:
            mtbf_hours = (
                sum(intervals_in_hours, Decimal("0")) / Decimal(len(intervals_in_hours))
            ).quantize(Decimal("0.01"))

        return MaintenanceFailureAnalysisReportRead(
            generated_at=generated_at,
            failure_count=failure_count,
            open_failure_count=open_failure_count,
            under_analysis_count=under_analysis_count,
            resolved_failure_count=resolved_failure_count,
            closed_failure_count=closed_failure_count,
            repeat_failure_count=repeat_failure_count,
            repeat_failure_rate_pct=repeat_failure_rate_pct,
            rca_completed_count=rca_completed_count,
            rca_pending_count=rca_pending_count,
            rca_completion_rate_pct=rca_completion_rate_pct,
            caused_shutdown_count=caused_shutdown_count,
            safety_incident_count=safety_incident_count,
            total_downtime_minutes=total_downtime_minutes,
            average_downtime_minutes=average_downtime_minutes,
            mtbf_hours=mtbf_hours,
            top_failure_modes=[
                MaintenanceFailureAnalysisBucketRead(**item)
                for item in summary["top_failure_modes"]
            ],
            top_root_causes=[
                MaintenanceFailureAnalysisBucketRead(**item)
                for item in summary["top_root_causes"]
            ],
            top_assets=[
                MaintenanceFailureAnalysisAssetRead(**item)
                for item in summary["top_assets"]
            ],
        )

    def _validate_checklist_result_entry(
        self,
        template_item: MaintenanceChecklistTemplateItem,
        entry: MaintenanceChecklistResultEntryCreate,
    ) -> None:
        response_type = template_item.response_type
        if response_type in {
            ChecklistResponseType.PASS_FAIL.value,
            ChecklistResponseType.YES_NO.value,
        } and entry.boolean_value is None:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_RESULT_INVALID",
                message="Checklist item boolean wajib memiliki boolean_value.",
                status_code=422,
            )
        if response_type == ChecklistResponseType.NUMERIC.value and entry.numeric_value is None:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_RESULT_INVALID",
                message="Checklist item numeric wajib memiliki numeric_value.",
                status_code=422,
            )
        if response_type in {
            ChecklistResponseType.TEXT.value,
            ChecklistResponseType.MULTI_SELECT.value,
        } and not entry.text_value:
            raise AppError(
                code="MAINTENANCE_CHECKLIST_RESULT_INVALID",
                message="Checklist item text/multi_select wajib memiliki text_value.",
                status_code=422,
            )
        if response_type == ChecklistResponseType.METER_READING.value and (
            entry.numeric_value is None and entry.meter_reading_id is None
        ):
            raise AppError(
                code="MAINTENANCE_CHECKLIST_RESULT_INVALID",
                message=(
                    "Checklist item meter reading wajib memiliki numeric_value "
                    "atau meter_reading_id."
                ),
                status_code=422,
            )

    def _derive_result_status(
        self,
        template_item: MaintenanceChecklistTemplateItem,
        entry: MaintenanceChecklistResultEntryCreate,
    ) -> tuple[str, bool]:
        response_type = template_item.response_type
        if response_type == ChecklistResponseType.PASS_FAIL.value:
            is_abnormal = entry.boolean_value is False
            return (
                ChecklistResultStatus.FAIL.value
                if is_abnormal
                else ChecklistResultStatus.PASS.value
            ), is_abnormal
        if response_type == ChecklistResponseType.YES_NO.value:
            is_abnormal = entry.boolean_value is False
            return (
                ChecklistResultStatus.ABNORMAL.value
                if is_abnormal
                else ChecklistResultStatus.NORMAL.value
            ), is_abnormal
        if response_type in {
            ChecklistResponseType.NUMERIC.value,
            ChecklistResponseType.METER_READING.value,
        }:
            is_abnormal = False
            if entry.numeric_value is not None:
                if (
                    template_item.normal_min_value is not None
                    and entry.numeric_value < template_item.normal_min_value
                ) or (
                    template_item.normal_max_value is not None
                    and entry.numeric_value > template_item.normal_max_value
                ):
                    is_abnormal = True
            return (
                ChecklistResultStatus.ABNORMAL.value
                if is_abnormal
                else ChecklistResultStatus.NORMAL.value
            ), is_abnormal
        if entry.result_status is not None:
            is_abnormal = entry.result_status in {
                ChecklistResultStatus.FAIL,
                ChecklistResultStatus.ABNORMAL,
            }
            return entry.result_status.value, is_abnormal
        return ChecklistResultStatus.NORMAL.value, False

    def _generate_finding_number(self, execution_id: UUID, index: int) -> str:
        return f"FD-{str(execution_id).split('-')[0].upper()}-{index:03d}"

    async def _calculate_actual_part_cost(self, work_order_id) -> Decimal:
        total = Decimal("0")
        for usage in await self.part_usages.list_by_work_order(work_order_id):
            if usage.unit_cost is None:
                continue
            multiplier = (
                Decimal("-1")
                if usage.usage_type == MaintenancePartUsageType.RETURN.value
                else Decimal("1")
            )
            total += usage.quantity * usage.unit_cost * multiplier
        return total

    async def _calculate_actual_labor_cost(self, work_order_id) -> Decimal:
        total = Decimal("0")
        for log in await self.labor_logs.list_by_work_order(work_order_id):
            if log.labor_cost is not None:
                total += log.labor_cost
        return total

    async def _record_work_order_event(
        self,
        *,
        work_order_id,
        event_type: str,
        previous_status: str | None,
        new_status: str | None,
        event_at,
        performed_by=None,
        employee_id=None,
        reason: str | None = None,
        event_payload: dict | None = None,
    ) -> MaintenanceWorkOrderEvent:
        return await self.events.create(
            MaintenanceWorkOrderEvent(
                work_order_id=work_order_id,
                event_type=event_type,
                previous_status=previous_status,
                new_status=new_status,
                event_at=event_at,
                performed_by=performed_by,
                employee_id=employee_id,
                reason=reason,
                event_payload=event_payload,
            )
        )

    async def _get_symptom_code_or_raise(self, symptom_code_id: UUID) -> MaintenanceSymptomCode:
        item = await self.symptom_codes.get(symptom_code_id)
        if item is None:
            raise MaintenanceSymptomCodeNotFoundError(str(symptom_code_id))
        return item

    async def _get_failure_mode_or_raise(
        self,
        failure_mode_id: UUID,
    ) -> MaintenanceFailureMode:
        item = await self.failure_modes.get(failure_mode_id)
        if item is None:
            raise MaintenanceFailureModeNotFoundError(str(failure_mode_id))
        return item

    async def _get_root_cause_code_or_raise(
        self,
        root_cause_code_id: UUID,
    ) -> MaintenanceRootCauseCode:
        item = await self.root_cause_codes.get(root_cause_code_id)
        if item is None:
            raise MaintenanceRootCauseCodeNotFoundError(str(root_cause_code_id))
        return item

    async def _get_asset_or_raise(self, asset_id):
        asset = await self.assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))
        return asset

    async def _get_priority_or_raise(self, priority_id):
        priority = await self.priorities.get(priority_id)
        if priority is None:
            raise MaintenancePriorityNotFoundError(str(priority_id))
        return priority

    async def _get_location_or_raise(self, location_id):
        location = await self.asset_locations.get(location_id)
        if location is None:
            raise AssetLocationNotFoundError(str(location_id))
        return location

    async def _get_partner_or_raise(self, partner_id):
        partner = await self.partners.get(partner_id)
        if partner is None:
            raise BusinessPartnerNotFoundError(str(partner_id))
        return partner

    def _validate_schedule_window(self, scheduled_start_at, scheduled_end_at) -> None:
        if scheduled_end_at <= scheduled_start_at:
            raise AppError(
                code="MAINTENANCE_SCHEDULE_WINDOW_INVALID",
                message="scheduled_end_at harus lebih besar dari scheduled_start_at.",
                status_code=422,
            )

    async def _ensure_schedule_no_conflict(
        self,
        *,
        asset_id,
        scheduled_start_at,
        scheduled_end_at,
        maintenance_team_id,
        vendor_partner_id,
        exclude_schedule_id=None,
        error_code: str = "MAINTENANCE_SCHEDULE_OVERLAP",
    ) -> None:
        overlaps = await self.schedules.list_active_overlaps(
            asset_id=asset_id,
            scheduled_start_at=scheduled_start_at,
            scheduled_end_at=scheduled_end_at,
            maintenance_team_id=maintenance_team_id,
            vendor_partner_id=vendor_partner_id,
            exclude_schedule_id=exclude_schedule_id,
        )
        if overlaps:
            raise AppError(
                code=error_code,
                message=(
                    "Jadwal bentrok dengan asset, tim, atau vendor pada rentang waktu yang sama."
                ),
                status_code=409,
                details={"conflict_count": len(overlaps)},
            )

    def _increment_due_date(self, current_due_date, interval_value: int, interval_unit: str):
        if interval_unit == "DAY":
            return current_due_date + timedelta(days=interval_value)
        if interval_unit == "WEEK":
            return current_due_date + timedelta(weeks=interval_value)
        if interval_unit == "MONTH":
            return current_due_date + timedelta(days=30 * interval_value)
        if interval_unit == "YEAR":
            return current_due_date + timedelta(days=365 * interval_value)
        return current_due_date
