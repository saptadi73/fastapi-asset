from contextlib import asynccontextmanager
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.compat import UTC
from app.core.exceptions import AppError
from app.modules.maintenance.constants import (
    MaintenancePlanTriggerType,
    MaintenanceScheduleStatus,
)
from app.modules.maintenance.schemas import (
    MaintenancePlanCreate,
    MaintenancePlanGeneratePayload,
)
from app.modules.maintenance.service import MaintenanceService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.assets = SimpleNamespace(get=AsyncMock())
    svc.priorities = SimpleNamespace(get=AsyncMock())
    svc.teams = SimpleNamespace(get=AsyncMock())
    svc.partners = SimpleNamespace(get=AsyncMock())
    svc.plans = SimpleNamespace(create=AsyncMock(), get=AsyncMock(), update=AsyncMock())
    svc.plan_assets = SimpleNamespace(
        create=AsyncMock(),
        list_active_by_plan=AsyncMock(return_value=[]),
    )
    svc.schedules = SimpleNamespace(
        create=AsyncMock(),
        update=AsyncMock(),
        list_active_overlaps=AsyncMock(return_value=[]),
    )
    svc.work_orders = SimpleNamespace(create=AsyncMock(), list_by_asset=AsyncMock(return_value=[]))
    return svc


@pytest.mark.asyncio
async def test_create_plan_rejects_missing_scope(service: MaintenanceService) -> None:
    with pytest.raises(AppError) as exc_info:
        await service.create_plan(
            MaintenancePlanCreate(
                plan_code="PM-001",
                plan_name="Plan tanpa scope",
                maintenance_type="PREVENTIVE",
                trigger_type="CALENDAR",
                calendar_interval_value=30,
                calendar_interval_unit="DAY",
                default_priority_id=uuid4(),
                effective_from=date(2026, 7, 27),
            )
        )

    assert exc_info.value.code == "MAINTENANCE_PLAN_SCOPE_REQUIRED"


@pytest.mark.asyncio
async def test_create_plan_rejects_calendar_trigger_without_interval(
    service: MaintenanceService,
) -> None:
    asset_id = uuid4()
    priority_id = uuid4()
    service.assets.get.return_value = SimpleNamespace(id=asset_id)
    service.priorities.get.return_value = SimpleNamespace(id=priority_id)

    with pytest.raises(AppError) as exc_info:
        await service.create_plan(
            MaintenancePlanCreate(
                plan_code="PM-002",
                plan_name="Plan invalid",
                asset_id=asset_id,
                maintenance_type="PREVENTIVE",
                trigger_type=MaintenancePlanTriggerType.CALENDAR,
                default_priority_id=priority_id,
                effective_from=date(2026, 7, 27),
            )
        )

    assert exc_info.value.code == "MAINTENANCE_PLAN_TRIGGER_INVALID"


@pytest.mark.asyncio
async def test_generate_schedules_from_plan_rejects_empty_targets(
    service: MaintenanceService,
) -> None:
    plan = SimpleNamespace(
        id=uuid4(),
        asset_id=None,
        calendar_interval_value=30,
        calendar_interval_unit="DAY",
        estimated_duration_minutes=120,
        default_team_id=None,
        default_vendor_partner_id=None,
        maintenance_contract_id=None,
        default_priority_id=uuid4(),
        maintenance_type="PREVENTIVE",
        plan_code="PM-003",
        plan_name="Preventive Plan",
        auto_create_work_order=True,
        requires_approval=False,
        trigger_type="CALENDAR",
        next_due_date=date(2026, 7, 27),
    )
    service.get_plan = AsyncMock(return_value=plan)

    with pytest.raises(AppError) as exc_info:
        await service.generate_schedules_from_plan(
            plan.id,
            MaintenancePlanGeneratePayload(
                scheduled_start_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
                created_by=uuid4(),
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_PLAN_TARGETS_EMPTY"


@pytest.mark.asyncio
async def test_generate_schedules_from_plan_creates_schedule_and_work_order(
    service: MaintenanceService,
) -> None:
    asset_id = uuid4()
    plan_id = uuid4()
    priority_id = uuid4()
    plan = SimpleNamespace(
        id=plan_id,
        asset_id=asset_id,
        calendar_interval_value=30,
        calendar_interval_unit="DAY",
        estimated_duration_minutes=90,
        default_team_id=None,
        default_vendor_partner_id=None,
        maintenance_contract_id=None,
        default_priority_id=priority_id,
        maintenance_type="PREVENTIVE",
        plan_code="PM-004",
        plan_name="Preventive Bulanan",
        auto_create_work_order=True,
        requires_approval=False,
        trigger_type="CALENDAR",
        next_due_date=date(2026, 7, 27),
    )
    asset = SimpleNamespace(id=asset_id, company_id=uuid4())
    created_schedule = SimpleNamespace(id=uuid4())
    created_work_order = SimpleNamespace(id=uuid4())
    refreshed_schedule = SimpleNamespace(
        id=created_schedule.id,
        status=MaintenanceScheduleStatus.PLANNED.value,
    )

    service.get_plan = AsyncMock(return_value=plan)
    service.assets.get.return_value = asset
    service.schedules.create.return_value = created_schedule
    service.work_orders.create.return_value = created_work_order
    service.get_schedule = AsyncMock(return_value=refreshed_schedule)

    items = await service.generate_schedules_from_plan(
        plan.id,
        MaintenancePlanGeneratePayload(
            scheduled_start_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
            schedule_prefix="SCH",
            created_by=uuid4(),
        ),
    )

    assert items == [refreshed_schedule]
    service.schedules.create.assert_awaited_once()
    service.work_orders.create.assert_awaited_once()
    service.schedules.update.assert_awaited_once()
    service.plans.update.assert_awaited_once()

