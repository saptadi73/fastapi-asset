from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.assets.models import Asset
from app.modules.maintenance.models import (
    MaintenanceChecklistExecution,
    MaintenanceChecklistResult,
    MaintenanceChecklistTemplate,
    MaintenanceChecklistTemplateItem,
    MaintenanceDowntime,
    MaintenanceFinding,
    MaintenanceLaborLog,
    MaintenancePartUsage,
    MaintenancePlan,
    MaintenancePlanAsset,
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceRequestWorkOrder,
    MaintenanceSchedule,
    MaintenanceTeam,
    MaintenanceTeamMember,
    MaintenanceWorkOrder,
    MaintenanceWorkOrderAssignment,
    MaintenanceWorkOrderEvent,
)
from app.shared.pagination import PaginationParams


class MaintenancePriorityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenancePriority) -> MaintenancePriority:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, priority_id: UUID) -> MaintenancePriority | None:
        return await self.session.get(MaintenancePriority, priority_id)

    async def list(self) -> Sequence[MaintenancePriority]:
        result = await self.session.scalars(
            select(MaintenancePriority).order_by(
                MaintenancePriority.severity_level.desc(),
                MaintenancePriority.code.asc(),
            )
        )
        return result.all()


class MaintenancePlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenancePlan) -> MaintenancePlan:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=[
                "asset",
                "asset_category",
                "default_priority",
                "default_team",
                "default_vendor_partner",
                "plan_assets",
            ],
        )
        return item

    async def get(self, plan_id: UUID) -> MaintenancePlan | None:
        stmt = (
            select(MaintenancePlan)
            .options(
                selectinload(MaintenancePlan.asset),
                selectinload(MaintenancePlan.asset_category),
                selectinload(MaintenancePlan.default_priority),
                selectinload(MaintenancePlan.default_team),
                selectinload(MaintenancePlan.default_vendor_partner),
                selectinload(MaintenancePlan.plan_assets).selectinload(
                    MaintenancePlanAsset.asset
                ),
            )
            .where(MaintenancePlan.id == plan_id)
        )
        return await self.session.scalar(stmt)

    async def list(self, pagination: PaginationParams) -> tuple[Sequence[MaintenancePlan], int]:
        stmt: Select[tuple[MaintenancePlan]] = select(MaintenancePlan).options(
            selectinload(MaintenancePlan.asset),
            selectinload(MaintenancePlan.asset_category),
            selectinload(MaintenancePlan.default_priority),
            selectinload(MaintenancePlan.default_team),
            selectinload(MaintenancePlan.default_vendor_partner),
            selectinload(MaintenancePlan.plan_assets),
        )
        count_stmt = select(func.count()).select_from(MaintenancePlan)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                MaintenancePlan.plan_code.ilike(search_value),
                MaintenancePlan.plan_name.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        sort_column = getattr(MaintenancePlan, pagination.sort or "plan_code")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(self, item: MaintenancePlan, **changes: object) -> MaintenancePlan:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=[
                "asset",
                "asset_category",
                "default_priority",
                "default_team",
                "default_vendor_partner",
                "plan_assets",
            ],
        )
        return item


class MaintenancePlanAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenancePlanAsset) -> MaintenancePlanAsset:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_active_by_plan(self, plan_id: UUID) -> Sequence[MaintenancePlanAsset]:
        stmt = (
            select(MaintenancePlanAsset)
            .options(selectinload(MaintenancePlanAsset.asset))
            .where(
                MaintenancePlanAsset.maintenance_plan_id == plan_id,
                MaintenancePlanAsset.is_active.is_(True),
            )
            .order_by(MaintenancePlanAsset.effective_from.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceChecklistTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceChecklistTemplate) -> MaintenanceChecklistTemplate:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["asset_category", "items"])
        return item

    async def get(self, template_id: UUID) -> MaintenanceChecklistTemplate | None:
        stmt = (
            select(MaintenanceChecklistTemplate)
            .options(
                selectinload(MaintenanceChecklistTemplate.asset_category),
                selectinload(MaintenanceChecklistTemplate.items),
            )
            .where(MaintenanceChecklistTemplate.id == template_id)
        )
        return await self.session.scalar(stmt)


class MaintenanceChecklistTemplateItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        item: MaintenanceChecklistTemplateItem,
    ) -> MaintenanceChecklistTemplateItem:
        self.session.add(item)
        await self.session.flush()
        return item


class MaintenanceChecklistExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        item: MaintenanceChecklistExecution,
    ) -> MaintenanceChecklistExecution:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["template", "work_order", "asset", "results"],
        )
        return item

    async def get(self, checklist_id: UUID) -> MaintenanceChecklistExecution | None:
        stmt = (
            select(MaintenanceChecklistExecution)
            .options(
                selectinload(MaintenanceChecklistExecution.template).selectinload(
                    MaintenanceChecklistTemplate.items
                ),
                selectinload(MaintenanceChecklistExecution.work_order),
                selectinload(MaintenanceChecklistExecution.asset),
                selectinload(MaintenanceChecklistExecution.results).selectinload(
                    MaintenanceChecklistResult.template_item
                ),
                selectinload(MaintenanceChecklistExecution.results).selectinload(
                    MaintenanceChecklistResult.findings
                ).selectinload(MaintenanceFinding.asset),
                selectinload(MaintenanceChecklistExecution.results).selectinload(
                    MaintenanceChecklistResult.findings
                ).selectinload(MaintenanceFinding.generated_request),
                selectinload(MaintenanceChecklistExecution.results).selectinload(
                    MaintenanceChecklistResult.findings
                ),
            )
            .where(MaintenanceChecklistExecution.id == checklist_id)
        )
        return await self.session.scalar(stmt)

    async def update(
        self,
        item: MaintenanceChecklistExecution,
        **changes: object,
    ) -> MaintenanceChecklistExecution:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["template", "work_order", "asset", "results"],
        )
        return item

    async def list_by_work_order(
        self,
        work_order_id: UUID,
    ) -> Sequence[MaintenanceChecklistExecution]:
        stmt = (
            select(MaintenanceChecklistExecution)
            .options(selectinload(MaintenanceChecklistExecution.results))
            .where(MaintenanceChecklistExecution.work_order_id == work_order_id)
            .order_by(MaintenanceChecklistExecution.started_at.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceChecklistResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceChecklistResult) -> MaintenanceChecklistResult:
        self.session.add(item)
        await self.session.flush()
        return item


class MaintenanceFindingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceFinding) -> MaintenanceFinding:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["checklist_result", "work_order", "asset", "generated_request"],
        )
        return item

    async def get(self, finding_id: UUID) -> MaintenanceFinding | None:
        stmt = (
            select(MaintenanceFinding)
            .options(
                selectinload(MaintenanceFinding.checklist_result).selectinload(
                    MaintenanceChecklistResult.template_item
                ),
                selectinload(MaintenanceFinding.work_order).selectinload(
                    MaintenanceWorkOrder.requests
                ),
                selectinload(MaintenanceFinding.asset),
                selectinload(MaintenanceFinding.generated_request),
            )
            .where(MaintenanceFinding.id == finding_id)
        )
        return await self.session.scalar(stmt)

    async def update(self, item: MaintenanceFinding, **changes: object) -> MaintenanceFinding:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["checklist_result", "work_order", "asset", "generated_request"],
        )
        return item

    async def list_by_work_order(self, work_order_id: UUID) -> Sequence[MaintenanceFinding]:
        stmt = (
            select(MaintenanceFinding)
            .options(
                selectinload(MaintenanceFinding.checklist_result),
                selectinload(MaintenanceFinding.generated_request),
            )
            .where(MaintenanceFinding.work_order_id == work_order_id)
            .order_by(MaintenanceFinding.reported_at.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceRequest) -> MaintenanceRequest:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["asset", "priority", "asset_location", "work_orders"],
        )
        return item

    async def get(self, request_id: UUID) -> MaintenanceRequest | None:
        stmt = (
            select(MaintenanceRequest)
            .options(
                selectinload(MaintenanceRequest.asset),
                selectinload(MaintenanceRequest.priority),
                selectinload(MaintenanceRequest.asset_location),
                selectinload(MaintenanceRequest.work_orders).selectinload(
                    MaintenanceRequestWorkOrder.work_order
                ),
            )
            .where(MaintenanceRequest.id == request_id)
        )
        return await self.session.scalar(stmt)

    async def list(self, pagination: PaginationParams) -> tuple[Sequence[MaintenanceRequest], int]:
        stmt: Select[tuple[MaintenanceRequest]] = select(MaintenanceRequest).options(
            selectinload(MaintenanceRequest.asset),
            selectinload(MaintenanceRequest.priority),
            selectinload(MaintenanceRequest.asset_location),
            selectinload(MaintenanceRequest.work_orders),
        )
        count_stmt = select(func.count()).select_from(MaintenanceRequest)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                MaintenanceRequest.request_number.ilike(search_value),
                MaintenanceRequest.title.ilike(search_value),
                MaintenanceRequest.problem_description.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        sort_column = getattr(MaintenanceRequest, pagination.sort or "reported_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(self, item: MaintenanceRequest, **changes: object) -> MaintenanceRequest:
        for key, value in changes.items():
            setattr(item, key, value)
        item.version += 1
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=["asset", "priority", "asset_location", "work_orders"],
        )
        return item


class MaintenanceWorkOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceWorkOrder) -> MaintenanceWorkOrder:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=[
                "asset",
                "priority",
                "requests",
                "assignments",
                "part_usages",
                "labor_logs",
                "downtimes",
                "events",
            ],
        )
        return item

    async def get(self, work_order_id: UUID) -> MaintenanceWorkOrder | None:
        stmt = (
            select(MaintenanceWorkOrder)
            .options(
                selectinload(MaintenanceWorkOrder.asset),
                selectinload(MaintenanceWorkOrder.priority),
                selectinload(MaintenanceWorkOrder.vendor_partner),
                selectinload(MaintenanceWorkOrder.requests).selectinload(
                    MaintenanceRequestWorkOrder.request
                ),
                selectinload(MaintenanceWorkOrder.assignments),
                selectinload(MaintenanceWorkOrder.part_usages),
                selectinload(MaintenanceWorkOrder.labor_logs),
                selectinload(MaintenanceWorkOrder.downtimes),
                selectinload(MaintenanceWorkOrder.events),
            )
            .where(MaintenanceWorkOrder.id == work_order_id)
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        pagination: PaginationParams,
    ) -> tuple[Sequence[MaintenanceWorkOrder], int]:
        stmt: Select[tuple[MaintenanceWorkOrder]] = select(MaintenanceWorkOrder).options(
            selectinload(MaintenanceWorkOrder.asset),
            selectinload(MaintenanceWorkOrder.priority),
            selectinload(MaintenanceWorkOrder.requests),
            selectinload(MaintenanceWorkOrder.assignments),
            selectinload(MaintenanceWorkOrder.part_usages),
            selectinload(MaintenanceWorkOrder.labor_logs),
            selectinload(MaintenanceWorkOrder.downtimes),
            selectinload(MaintenanceWorkOrder.events),
        )
        count_stmt = select(func.count()).select_from(MaintenanceWorkOrder)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                MaintenanceWorkOrder.work_order_number.ilike(search_value),
                MaintenanceWorkOrder.title.ilike(search_value),
                MaintenanceWorkOrder.scope_of_work.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        sort_column = getattr(MaintenanceWorkOrder, pagination.sort or "created_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def list_by_asset(self, asset_id: UUID) -> Sequence[MaintenanceWorkOrder]:
        stmt = (
            select(MaintenanceWorkOrder)
            .options(
                selectinload(MaintenanceWorkOrder.asset),
                selectinload(MaintenanceWorkOrder.priority),
                selectinload(MaintenanceWorkOrder.requests),
                selectinload(MaintenanceWorkOrder.assignments),
                selectinload(MaintenanceWorkOrder.part_usages),
                selectinload(MaintenanceWorkOrder.labor_logs),
                selectinload(MaintenanceWorkOrder.downtimes),
                selectinload(MaintenanceWorkOrder.events),
            )
            .where(MaintenanceWorkOrder.asset_id == asset_id)
            .order_by(
                MaintenanceWorkOrder.closed_at.desc(),
                MaintenanceWorkOrder.actual_end_at.desc(),
                MaintenanceWorkOrder.actual_start_at.desc(),
                MaintenanceWorkOrder.planned_start_at.desc(),
                MaintenanceWorkOrder.created_at.desc(),
            )
        )
        items = await self.session.scalars(stmt)
        return items.all()

    async def update(self, item: MaintenanceWorkOrder, **changes: object) -> MaintenanceWorkOrder:
        for key, value in changes.items():
            setattr(item, key, value)
        item.version += 1
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=[
                "asset",
                "priority",
                "requests",
                "assignments",
                "part_usages",
                "labor_logs",
                "downtimes",
                "events",
            ],
        )
        return item


class MaintenancePartUsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenancePartUsage) -> MaintenancePartUsage:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_work_order(self, work_order_id: UUID) -> Sequence[MaintenancePartUsage]:
        stmt = (
            select(MaintenancePartUsage)
            .where(MaintenancePartUsage.work_order_id == work_order_id)
            .order_by(MaintenancePartUsage.used_at.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceLaborLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceLaborLog) -> MaintenanceLaborLog:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_work_order(self, work_order_id: UUID) -> Sequence[MaintenanceLaborLog]:
        stmt = (
            select(MaintenanceLaborLog)
            .where(MaintenanceLaborLog.work_order_id == work_order_id)
            .order_by(MaintenanceLaborLog.started_at.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceDowntimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceDowntime) -> MaintenanceDowntime:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["asset", "request", "work_order"])
        return item

    async def list_by_work_order(self, work_order_id: UUID) -> Sequence[MaintenanceDowntime]:
        stmt = (
            select(MaintenanceDowntime)
            .options(
                selectinload(MaintenanceDowntime.asset),
                selectinload(MaintenanceDowntime.request),
            )
            .where(MaintenanceDowntime.work_order_id == work_order_id)
            .order_by(MaintenanceDowntime.started_at.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceWorkOrderEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceWorkOrderEvent) -> MaintenanceWorkOrderEvent:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_by_work_order(self, work_order_id: UUID) -> Sequence[MaintenanceWorkOrderEvent]:
        stmt = (
            select(MaintenanceWorkOrderEvent)
            .where(MaintenanceWorkOrderEvent.work_order_id == work_order_id)
            .order_by(MaintenanceWorkOrderEvent.event_at.asc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class MaintenanceReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_backlog_summary(self, *, as_of: datetime) -> dict[str, int]:
        request_backlog_statuses = [
            "SUBMITTED",
            "TRIAGE",
            "WAITING_INFORMATION",
            "APPROVED",
            "IN_PROGRESS",
        ]
        request_terminal_statuses = [
            "REJECTED",
            "CONVERTED_TO_WORK_ORDER",
            "RESOLVED",
            "CLOSED",
            "CANCELLED",
        ]
        active_schedule_statuses = ["PLANNED", "CONFIRMED", "DISPATCHED", "IN_PROGRESS"]

        request_backlog_count = await self.session.scalar(
            select(func.count())
            .select_from(MaintenanceRequest)
            .where(MaintenanceRequest.status.in_(request_backlog_statuses))
        )
        overdue_request_count = await self.session.scalar(
            select(func.count())
            .select_from(MaintenanceRequest)
            .where(
                MaintenanceRequest.required_response_at.is_not(None),
                MaintenanceRequest.required_response_at < as_of,
                not_(MaintenanceRequest.status.in_(request_terminal_statuses)),
            )
        )
        open_work_order_count = await self.session.scalar(
            select(func.count())
            .select_from(MaintenanceWorkOrder)
            .where(not_(MaintenanceWorkOrder.status.in_(["CLOSED", "CANCELLED"])))
        )
        overdue_work_order_count = await self.session.scalar(
            select(func.count())
            .select_from(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.planned_end_at.is_not(None),
                MaintenanceWorkOrder.planned_end_at < as_of,
                not_(
                    MaintenanceWorkOrder.status.in_(
                        ["COMPLETED", "VERIFICATION", "CLOSED", "CANCELLED"]
                    )
                ),
            )
        )
        active_schedule_count = await self.session.scalar(
            select(func.count())
            .select_from(MaintenanceSchedule)
            .where(MaintenanceSchedule.status.in_(active_schedule_statuses))
        )
        overdue_schedule_count = await self.session.scalar(
            select(func.count())
            .select_from(MaintenanceSchedule)
            .where(
                MaintenanceSchedule.scheduled_end_at < as_of,
                MaintenanceSchedule.status.in_(active_schedule_statuses),
            )
        )
        return {
            "request_backlog_count": request_backlog_count or 0,
            "overdue_request_count": overdue_request_count or 0,
            "open_work_order_count": open_work_order_count or 0,
            "overdue_work_order_count": overdue_work_order_count or 0,
            "active_schedule_count": active_schedule_count or 0,
            "overdue_schedule_count": overdue_schedule_count or 0,
        }

    async def get_sla_summary(
        self,
        *,
        as_of: datetime,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, int]:
        response_stmt = select(MaintenanceRequest).where(
            MaintenanceRequest.required_response_at.is_not(None)
        )
        resolution_stmt = select(MaintenanceRequest).where(
            MaintenanceRequest.required_resolution_at.is_not(None)
        )

        if date_from is not None:
            response_stmt = response_stmt.where(MaintenanceRequest.reported_at >= date_from)
            resolution_stmt = resolution_stmt.where(MaintenanceRequest.reported_at >= date_from)

        if date_to is not None:
            response_stmt = response_stmt.where(MaintenanceRequest.reported_at <= date_to)
            resolution_stmt = resolution_stmt.where(MaintenanceRequest.reported_at <= date_to)

        response_items = (await self.session.scalars(response_stmt)).all()
        resolution_items = (await self.session.scalars(resolution_stmt)).all()

        response_met_count = sum(
            1
            for item in response_items
            if item.triaged_at is not None and item.triaged_at <= item.required_response_at
        )
        response_breached_count = sum(
            1
            for item in response_items
            if (item.triaged_at is not None and item.triaged_at > item.required_response_at)
            or (
                item.triaged_at is None
                and item.status not in ["REJECTED", "CANCELLED"]
                and item.required_response_at < as_of
            )
        )

        resolution_met_count = sum(
            1
            for item in resolution_items
            if (
                item.status in ["RESOLVED", "CLOSED", "CONVERTED_TO_WORK_ORDER"]
                and item.updated_at <= item.required_resolution_at
            )
        )
        resolution_breached_count = sum(
            1
            for item in resolution_items
            if (
                item.status in ["RESOLVED", "CLOSED", "CONVERTED_TO_WORK_ORDER"]
                and item.updated_at > item.required_resolution_at
            )
            or (
                item.status not in ["RESOLVED", "CLOSED", "REJECTED", "CANCELLED"]
                and item.required_resolution_at < as_of
            )
        )

        return {
            "response_sla_target_count": len(response_items),
            "response_sla_met_count": response_met_count,
            "response_sla_breached_count": response_breached_count,
            "resolution_sla_target_count": len(resolution_items),
            "resolution_sla_met_count": resolution_met_count,
            "resolution_sla_breached_count": resolution_breached_count,
        }

    async def get_reliability_summary(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, int | Decimal]:
        work_order_stmt = select(MaintenanceWorkOrder).where(
            MaintenanceWorkOrder.actual_start_at.is_not(None),
            MaintenanceWorkOrder.actual_end_at.is_not(None),
        )
        downtime_stmt = select(MaintenanceDowntime)

        if date_from is not None:
            work_order_stmt = work_order_stmt.where(
                MaintenanceWorkOrder.actual_end_at >= date_from
            )
            downtime_stmt = downtime_stmt.where(MaintenanceDowntime.started_at >= date_from)

        if date_to is not None:
            work_order_stmt = work_order_stmt.where(MaintenanceWorkOrder.actual_end_at <= date_to)
            downtime_stmt = downtime_stmt.where(MaintenanceDowntime.started_at <= date_to)

        work_orders = (await self.session.scalars(work_order_stmt)).all()
        downtimes = (await self.session.scalars(downtime_stmt)).all()

        completed_repairs = [
            item for item in work_orders if item.status in ["COMPLETED", "VERIFICATION", "CLOSED"]
        ]
        breakdown_work_order_count = len(
            [item for item in work_orders if item.maintenance_type == "BREAKDOWN"]
        )
        preventive_work_order_count = len(
            [item for item in work_orders if item.maintenance_type == "PREVENTIVE"]
        )
        unplanned_work_order_count = len(
            [
                item
                for item in work_orders
                if item.maintenance_type in ["BREAKDOWN", "CORRECTIVE", "EMERGENCY"]
            ]
        )
        planned_work_order_count = len(work_orders) - unplanned_work_order_count

        total_repair_minutes = sum(
            int((item.actual_end_at - item.actual_start_at).total_seconds() // 60)
            for item in completed_repairs
        )
        total_downtime_minutes = sum(item.duration_minutes or 0 for item in downtimes)
        repeat_failure_asset_count = len(
            {
                item.asset_id
                for item in work_orders
                if item.maintenance_type in ["BREAKDOWN", "CORRECTIVE", "EMERGENCY"]
            }
        )

        return {
            "completed_repair_count": len(completed_repairs),
            "breakdown_work_order_count": breakdown_work_order_count,
            "preventive_work_order_count": preventive_work_order_count,
            "unplanned_work_order_count": unplanned_work_order_count,
            "planned_work_order_count": planned_work_order_count,
            "total_repair_minutes": total_repair_minutes,
            "total_downtime_minutes": total_downtime_minutes,
            "downtime_count": len(downtimes),
            "repeat_failure_asset_count": repeat_failure_asset_count,
        }

    async def list_cost_report(
        self,
        pagination: PaginationParams,
        *,
        asset_id: UUID | None = None,
        maintenance_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[Sequence[MaintenanceWorkOrder], int]:
        stmt: Select[tuple[MaintenanceWorkOrder]] = (
            select(MaintenanceWorkOrder)
            .options(selectinload(MaintenanceWorkOrder.asset))
        )
        count_stmt = select(func.count()).select_from(MaintenanceWorkOrder)

        if pagination.search:
            search_value = f"%{pagination.search}%"
            stmt = stmt.join(MaintenanceWorkOrder.asset)
            count_stmt = count_stmt.join(MaintenanceWorkOrder.asset)
            search_filter = or_(
                MaintenanceWorkOrder.work_order_number.ilike(search_value),
                MaintenanceWorkOrder.title.ilike(search_value),
                MaintenanceWorkOrder.maintenance_type.ilike(search_value),
                Asset.asset_code.ilike(search_value),
                Asset.asset_name.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if asset_id is not None:
            stmt = stmt.where(MaintenanceWorkOrder.asset_id == asset_id)
            count_stmt = count_stmt.where(MaintenanceWorkOrder.asset_id == asset_id)

        if maintenance_type is not None:
            stmt = stmt.where(MaintenanceWorkOrder.maintenance_type == maintenance_type)
            count_stmt = count_stmt.where(MaintenanceWorkOrder.maintenance_type == maintenance_type)

        if date_from is not None:
            date_filter = or_(
                MaintenanceWorkOrder.actual_end_at >= date_from,
                MaintenanceWorkOrder.closed_at >= date_from,
            )
            stmt = stmt.where(date_filter)
            count_stmt = count_stmt.where(date_filter)

        if date_to is not None:
            date_filter = or_(
                MaintenanceWorkOrder.actual_end_at <= date_to,
                MaintenanceWorkOrder.closed_at <= date_to,
            )
            stmt = stmt.where(date_filter)
            count_stmt = count_stmt.where(date_filter)

        sort_column = getattr(MaintenanceWorkOrder, pagination.sort or "closed_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items


class MaintenanceRequestWorkOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceRequestWorkOrder) -> MaintenanceRequestWorkOrder:
        self.session.add(item)
        await self.session.flush()
        return item


class MaintenanceWorkOrderAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceWorkOrderAssignment) -> MaintenanceWorkOrderAssignment:
        self.session.add(item)
        await self.session.flush()
        return item


class MaintenanceTeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceTeam) -> MaintenanceTeam:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item, attribute_names=["default_location", "members"])
        return item

    async def get(self, team_id: UUID) -> MaintenanceTeam | None:
        stmt = (
            select(MaintenanceTeam)
            .options(
                selectinload(MaintenanceTeam.default_location),
                selectinload(MaintenanceTeam.members),
            )
            .where(MaintenanceTeam.id == team_id)
        )
        return await self.session.scalar(stmt)

    async def list(self, pagination: PaginationParams) -> tuple[Sequence[MaintenanceTeam], int]:
        stmt: Select[tuple[MaintenanceTeam]] = select(MaintenanceTeam).options(
            selectinload(MaintenanceTeam.default_location),
            selectinload(MaintenanceTeam.members),
        )
        count_stmt = select(func.count()).select_from(MaintenanceTeam)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                MaintenanceTeam.team_code.ilike(search_value),
                MaintenanceTeam.team_name.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        sort_column = getattr(MaintenanceTeam, pagination.sort or "team_code")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items


class MaintenanceTeamMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceTeamMember) -> MaintenanceTeamMember:
        self.session.add(item)
        await self.session.flush()
        return item


class MaintenanceScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: MaintenanceSchedule) -> MaintenanceSchedule:
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=[
                "asset",
                "request",
                "work_order",
                "maintenance_team",
                "vendor_partner",
            ],
        )
        return item

    async def get(self, schedule_id: UUID) -> MaintenanceSchedule | None:
        stmt = (
            select(MaintenanceSchedule)
            .options(
                selectinload(MaintenanceSchedule.asset),
                selectinload(MaintenanceSchedule.request),
                selectinload(MaintenanceSchedule.work_order),
                selectinload(MaintenanceSchedule.maintenance_team),
                selectinload(MaintenanceSchedule.vendor_partner),
            )
            .where(MaintenanceSchedule.id == schedule_id)
        )
        return await self.session.scalar(stmt)

    async def list(self, pagination: PaginationParams) -> tuple[Sequence[MaintenanceSchedule], int]:
        stmt: Select[tuple[MaintenanceSchedule]] = select(MaintenanceSchedule).options(
            selectinload(MaintenanceSchedule.asset),
            selectinload(MaintenanceSchedule.request),
            selectinload(MaintenanceSchedule.work_order),
            selectinload(MaintenanceSchedule.maintenance_team),
            selectinload(MaintenanceSchedule.vendor_partner),
        )
        count_stmt = select(func.count()).select_from(MaintenanceSchedule)
        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                MaintenanceSchedule.schedule_number.ilike(search_value),
                MaintenanceSchedule.status.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        sort_column = getattr(MaintenanceSchedule, pagination.sort or "scheduled_start_at")
        if pagination.order == "desc":
            sort_column = sort_column.desc()
        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(self, item: MaintenanceSchedule, **changes: object) -> MaintenanceSchedule:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(
            item,
            attribute_names=[
                "asset",
                "request",
                "work_order",
                "maintenance_team",
                "vendor_partner",
            ],
        )
        return item

    async def list_active_overlaps(
        self,
        *,
        asset_id: UUID,
        scheduled_start_at,
        scheduled_end_at,
        maintenance_team_id: UUID | None,
        vendor_partner_id: UUID | None,
        exclude_schedule_id: UUID | None = None,
    ) -> Sequence[MaintenanceSchedule]:
        active_statuses = ["PLANNED", "CONFIRMED", "DISPATCHED", "IN_PROGRESS"]
        stmt = select(MaintenanceSchedule).where(
            MaintenanceSchedule.status.in_(active_statuses),
            MaintenanceSchedule.scheduled_start_at < scheduled_end_at,
            MaintenanceSchedule.scheduled_end_at > scheduled_start_at,
            or_(
                MaintenanceSchedule.asset_id == asset_id,
                MaintenanceSchedule.maintenance_team_id == maintenance_team_id
                if maintenance_team_id is not None
                else False,
                MaintenanceSchedule.vendor_partner_id == vendor_partner_id
                if vendor_partner_id is not None
                else False,
            ),
        )
        if exclude_schedule_id is not None:
            stmt = stmt.where(MaintenanceSchedule.id != exclude_schedule_id)
        result = await self.session.scalars(stmt)
        return result.all()
