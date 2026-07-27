from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.maintenance.models import (
    MaintenanceChecklistExecution,
    MaintenanceChecklistResult,
    MaintenanceChecklistTemplate,
    MaintenanceChecklistTemplateItem,
    MaintenanceFinding,
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
            attribute_names=["asset", "priority", "requests", "assignments"],
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
            attribute_names=["asset", "priority", "requests", "assignments"],
        )
        return item


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
