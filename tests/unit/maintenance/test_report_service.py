from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.maintenance.service import MaintenanceService
from app.shared.pagination import PaginationParams


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.reports = SimpleNamespace(
        get_backlog_summary=AsyncMock(
            return_value={
                "request_backlog_count": 5,
                "overdue_request_count": 2,
                "open_work_order_count": 8,
                "overdue_work_order_count": 3,
                "active_schedule_count": 6,
                "overdue_schedule_count": 1,
            }
        ),
        list_cost_report=AsyncMock(return_value=([], 0)),
    )
    return svc


@pytest.mark.asyncio
async def test_get_backlog_report_maps_repository_summary(
    service: MaintenanceService,
) -> None:
    item = await service.get_backlog_report()

    assert item.request_backlog_count == 5
    assert item.overdue_work_order_count == 3
    service.reports.get_backlog_summary.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_cost_report_serializes_work_orders(service: MaintenanceService) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        work_order_number="WO-REP-001",
        asset_id=uuid4(),
        maintenance_type="CORRECTIVE",
        status="CLOSED",
        currency_code="IDR",
        actual_part_cost=250000,
        actual_labor_cost=150000,
        actual_vendor_cost=100000,
        actual_end_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
        closed_at=datetime(2026, 7, 27, 11, 0, tzinfo=UTC),
        asset=SimpleNamespace(
            id=uuid4(),
            asset_code="AST-001",
            asset_name="Pompa Utility",
        ),
    )
    service.reports.list_cost_report.return_value = ([work_order], 1)

    items, total_items = await service.get_cost_report(
        PaginationParams(page=1, page_size=20, search=None, sort="closed_at", order="desc")
    )

    assert total_items == 1
    assert items[0].work_order_number == "WO-REP-001"
    assert items[0].total_actual_cost == 500000
