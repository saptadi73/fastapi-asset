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
    MaintenanceRequestStatus,
    MaintenanceScheduleStatus,
    MaintenanceWorkOrderStatus,
)
from app.modules.maintenance.exceptions import (
    MaintenancePriorityNotFoundError,
    MaintenanceRequestNotFoundError,
    MaintenanceScheduleNotFoundError,
    MaintenanceTeamNotFoundError,
    MaintenanceWorkOrderNotFoundError,
)
from app.modules.maintenance.models import (
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceRequestWorkOrder,
    MaintenanceSchedule,
    MaintenanceTeam,
    MaintenanceTeamMember,
    MaintenanceWorkOrder,
    MaintenanceWorkOrderAssignment,
)
from app.modules.maintenance.repository import (
    MaintenancePriorityRepository,
    MaintenanceRequestRepository,
    MaintenanceRequestWorkOrderRepository,
    MaintenanceScheduleRepository,
    MaintenanceTeamMemberRepository,
    MaintenanceTeamRepository,
    MaintenanceWorkOrderAssignmentRepository,
    MaintenanceWorkOrderRepository,
)
from app.modules.maintenance.schemas import (
    MaintenanceConvertToWorkOrderPayload,
    MaintenancePriorityCreate,
    MaintenanceRequestActionPayload,
    MaintenanceRequestCreate,
    MaintenanceRequestRejectPayload,
    MaintenanceRequestTriagePayload,
    MaintenanceScheduleConfirmPayload,
    MaintenanceScheduleCreate,
    MaintenanceScheduleReschedulePayload,
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
            async with self.session.begin():
                await self.teams.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_TEAM_CONFLICT",
                message="Team code sudah digunakan pada company yang sama.",
                status_code=409,
            ) from exc
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
            async with self.session.begin():
                await self.team_members.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_TEAM_MEMBER_CONFLICT",
                message="Member tim dengan periode efektif yang sama sudah ada.",
                status_code=409,
            ) from exc
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
            async with self.session.begin():
                await self.schedules.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_SCHEDULE_CONFLICT",
                message="Schedule number sudah digunakan.",
                status_code=409,
            ) from exc
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
        async with self.session.begin():
            await self.schedules.update(
                item,
                status=MaintenanceScheduleStatus.CONFIRMED.value,
                confirmed_at=payload.acted_at,
            )
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
        async with self.session.begin():
            await self.schedules.update(
                item,
                scheduled_start_at=payload.scheduled_start_at,
                scheduled_end_at=payload.scheduled_end_at,
                status=MaintenanceScheduleStatus.POSTPONED.value,
                reschedule_count=item.reschedule_count + 1,
                reschedule_reason=payload.reschedule_reason,
            )
        return await self.get_schedule(schedule_id)

    async def create_priority(self, payload: MaintenancePriorityCreate) -> MaintenancePriority:
        item = MaintenancePriority(**payload.model_dump())
        try:
            async with self.session.begin():
                await self.priorities.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_PRIORITY_CONFLICT",
                message="Code maintenance priority sudah digunakan.",
                status_code=409,
            ) from exc
        return item

    async def list_priorities(self) -> list[MaintenancePriority]:
        return list(await self.priorities.list())

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
            async with self.session.begin():
                await self.requests.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_REQUEST_CONFLICT",
                message="Request number maintenance sudah digunakan.",
                status_code=409,
            ) from exc
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
        async with self.session.begin():
            await self.requests.update(
                item,
                status=MaintenanceRequestStatus.SUBMITTED.value,
                updated_by=payload.actor_id,
            )
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
        async with self.session.begin():
            await self.requests.update(item, **changes)
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
        async with self.session.begin():
            await self.requests.update(
                item,
                status=MaintenanceRequestStatus.APPROVED.value,
                updated_by=payload.actor_id,
            )
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
        async with self.session.begin():
            await self.requests.update(
                item,
                status=MaintenanceRequestStatus.REJECTED.value,
                rejection_reason=payload.rejection_reason,
                updated_by=payload.actor_id,
            )
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
            async with self.session.begin():
                created = await self.work_orders.create(work_order)
                link.work_order_id = created.id
                await self.request_work_orders.create(link)
                await self.requests.update(
                    request,
                    status=MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER.value,
                    updated_by=payload.created_by,
                )
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CONFLICT",
                message="Work order number sudah digunakan atau terjadi konflik konversi.",
                status_code=409,
            ) from exc
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
            async with self.session.begin():
                await self.work_orders.create(item)
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_CONFLICT",
                message="Work order number sudah digunakan.",
                status_code=409,
            ) from exc
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
        async with self.session.begin():
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.APPROVED.value,
                approved_by=payload.actor_id,
                approved_at=payload.acted_at,
                updated_by=payload.actor_id,
            )
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
            async with self.session.begin():
                await self.assignments.create(assignment)
                await self.work_orders.update(
                    item,
                    status=MaintenanceWorkOrderStatus.ASSIGNED.value,
                    lead_technician_id=payload.employee_id
                    if payload.assignment_role.value == "LEAD_TECHNICIAN"
                    else item.lead_technician_id,
                    updated_by=payload.actor_id,
                )
        except IntegrityError as exc:
            raise AppError(
                code="MAINTENANCE_WORK_ORDER_ASSIGNMENT_CONFLICT",
                message="Assignment teknisi work order sudah ada.",
                status_code=409,
            ) from exc
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
        async with self.session.begin():
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
        async with self.session.begin():
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
        async with self.session.begin():
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.VERIFICATION.value,
                verified_by_employee_id=payload.actor_id,
                verified_at=payload.acted_at,
                updated_by=payload.actor_id,
            )
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
        asset = await self._get_asset_or_raise(item.asset_id)
        new_condition = item.asset_condition_after or asset.condition_status
        async with self.session.begin():
            await self.work_orders.update(
                item,
                status=MaintenanceWorkOrderStatus.CLOSED.value,
                closed_by=payload.actor_id,
                closed_at=payload.acted_at,
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
        return await self.get_work_order(work_order_id)

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
                code="MAINTENANCE_SCHEDULE_OVERLAP",
                message=(
                    "Jadwal bentrok dengan asset, tim, atau vendor pada rentang waktu yang sama."
                ),
                status_code=409,
                details={"conflict_count": len(overlaps)},
            )
