from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.modules.maintenance.constants import (
    ChecklistExecutionStatus,
    MaintenanceFindingStatus,
    MaintenanceWorkOrderStatus,
)
from app.modules.maintenance.schemas import (
    MaintenanceLaborLogCreate,
    MaintenancePartUsageCreate,
    MaintenanceRequestActionPayload,
)
from app.modules.maintenance.service import MaintenanceService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.requests = SimpleNamespace(update=AsyncMock())
    svc.work_orders = SimpleNamespace(
        create=AsyncMock(),
        update=AsyncMock(),
        get=AsyncMock(),
        list_by_asset=AsyncMock(return_value=[]),
    )
    svc.part_usages = SimpleNamespace(
        create=AsyncMock(),
        list_by_work_order=AsyncMock(return_value=[]),
    )
    svc.labor_logs = SimpleNamespace(
        create=AsyncMock(),
        list_by_work_order=AsyncMock(return_value=[]),
    )
    svc.events = SimpleNamespace(create=AsyncMock(), list_by_work_order=AsyncMock(return_value=[]))
    svc.checklist_executions = SimpleNamespace(list_by_work_order=AsyncMock(return_value=[]))
    svc.findings = SimpleNamespace(list_by_work_order=AsyncMock(return_value=[]))
    svc.assets = SimpleNamespace(get=AsyncMock(), update=AsyncMock())
    svc.asset_status_histories = SimpleNamespace(create=AsyncMock())
    return svc


@pytest.mark.asyncio
async def test_create_part_usage_updates_actual_part_cost(service: MaintenanceService) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        currency_code="IDR",
        updated_by=uuid4(),
    )
    service.get_work_order = AsyncMock(side_effect=[work_order, work_order])
    service.part_usages.list_by_work_order.return_value = [
        SimpleNamespace(
            quantity=Decimal("2"),
            unit_cost=Decimal("15000"),
            usage_type="CONSUME",
        )
    ]

    await service.create_part_usage(
        work_order.id,
        MaintenancePartUsageCreate(
            part_item_id=uuid4(),
            quantity=Decimal("2"),
            unit_cost=Decimal("15000"),
            usage_type="CONSUME",
            used_at=datetime.now(UTC),
        ),
    )

    assert service.work_orders.update.await_args.kwargs["actual_part_cost"] == Decimal("30000")


@pytest.mark.asyncio
async def test_create_labor_log_calculates_cost(service: MaintenanceService) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        updated_by=uuid4(),
    )
    service.get_work_order = AsyncMock(side_effect=[work_order, work_order])
    service.labor_logs.list_by_work_order.return_value = [
        SimpleNamespace(labor_cost=Decimal("100000"))
    ]

    await service.create_labor_log(
        work_order.id,
        MaintenanceLaborLogCreate(
            employee_id=uuid4(),
            started_at=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
            ended_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
            activity_type="REPAIR",
            hourly_rate=Decimal("50000"),
        ),
    )

    assert service.work_orders.update.await_args.kwargs["actual_labor_cost"] == Decimal("100000")


@pytest.mark.asyncio
async def test_close_work_order_rejects_incomplete_checklist(service: MaintenanceService) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        work_order_number="WO-001",
        status=MaintenanceWorkOrderStatus.VERIFICATION.value,
        requires_verification=True,
        actual_start_at=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
        actual_end_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
        completion_summary="Selesai",
    )
    service.get_work_order = AsyncMock(return_value=work_order)
    service.checklist_executions.list_by_work_order.return_value = [
        SimpleNamespace(status=ChecklistExecutionStatus.IN_PROGRESS.value)
    ]

    with pytest.raises(AppError) as exc_info:
        await service.close_work_order(
            work_order.id,
            MaintenanceRequestActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC)),
        )

    assert exc_info.value.code == "MAINTENANCE_WORK_ORDER_CLOSE_REQUIREMENTS_INCOMPLETE"


@pytest.mark.asyncio
async def test_close_work_order_rejects_pending_follow_up_finding(
    service: MaintenanceService,
) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        work_order_number="WO-002",
        status=MaintenanceWorkOrderStatus.VERIFICATION.value,
        requires_verification=True,
        actual_start_at=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
        actual_end_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
        completion_summary="Selesai",
    )
    service.get_work_order = AsyncMock(return_value=work_order)
    service.checklist_executions.list_by_work_order.return_value = [
        SimpleNamespace(status=ChecklistExecutionStatus.COMPLETED.value)
    ]
    service.findings.list_by_work_order.return_value = [
        SimpleNamespace(
            requires_follow_up=True,
            status=MaintenanceFindingStatus.OPEN.value,
            generated_request_id=None,
        )
    ]

    with pytest.raises(AppError) as exc_info:
        await service.close_work_order(
            work_order.id,
            MaintenanceRequestActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC)),
        )

    assert exc_info.value.code == "MAINTENANCE_WORK_ORDER_CLOSE_REQUIREMENTS_INCOMPLETE"
