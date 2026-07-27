from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.maintenance.constants import (
    MaintenanceWorkOrderEventType,
    MaintenanceWorkOrderStatus,
)
from app.modules.maintenance.schemas import MaintenanceDowntimeCreate
from app.modules.maintenance.service import MaintenanceService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.work_orders = SimpleNamespace(
        get=AsyncMock(),
        update=AsyncMock(),
        list_by_asset=AsyncMock(return_value=[]),
    )
    svc.downtimes = SimpleNamespace(
        create=AsyncMock(),
        list_by_work_order=AsyncMock(return_value=[]),
    )
    svc.events = SimpleNamespace(
        create=AsyncMock(),
        list_by_work_order=AsyncMock(return_value=[]),
    )
    return svc


@pytest.mark.asyncio
async def test_create_downtime_creates_event(service: MaintenanceService) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        requests=[],
    )
    refreshed = SimpleNamespace(id=work_order.id)
    service.get_work_order = AsyncMock(side_effect=[work_order, refreshed])

    result = await service.create_downtime(
        work_order.id,
        MaintenanceDowntimeCreate(
            downtime_type="UNPLANNED",
            started_at=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
            ended_at=datetime(2026, 7, 27, 9, 30, tzinfo=UTC),
            reason="Mesin berhenti mendadak",
        ),
    )

    assert result is refreshed
    service.downtimes.create.assert_awaited_once()
    service.events.create.assert_awaited_once()
    assert (
        service.events.create.await_args.args[0].event_type
        == MaintenanceWorkOrderEventType.DOWNTIME_RECORDED.value
    )


@pytest.mark.asyncio
async def test_list_work_order_events_returns_repository_items(
    service: MaintenanceService,
) -> None:
    work_order_id = uuid4()
    work_order = SimpleNamespace(id=work_order_id)
    event = SimpleNamespace(id=uuid4(), work_order_id=work_order_id)
    service.get_work_order = AsyncMock(return_value=work_order)
    service.events.list_by_work_order.return_value = [event]

    items = await service.list_work_order_events(work_order_id)

    assert items == [event]
