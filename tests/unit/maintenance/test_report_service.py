from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.compat import UTC
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
        get_sla_summary=AsyncMock(
            return_value={
                "response_sla_target_count": 10,
                "response_sla_met_count": 8,
                "response_sla_breached_count": 2,
                "resolution_sla_target_count": 6,
                "resolution_sla_met_count": 3,
                "resolution_sla_breached_count": 3,
            }
        ),
        get_reliability_summary=AsyncMock(
            return_value={
                "completed_repair_count": 4,
                "breakdown_work_order_count": 3,
                "preventive_work_order_count": 2,
                "unplanned_work_order_count": 5,
                "planned_work_order_count": 5,
                "total_repair_minutes": 600,
                "total_downtime_minutes": 240,
                "downtime_count": 3,
                "repeat_failure_asset_count": 2,
            }
        ),
        get_failure_analysis_summary=AsyncMock(
            return_value={
                "failure_count": 4,
                "open_failure_count": 1,
                "under_analysis_count": 1,
                "resolved_failure_count": 1,
                "closed_failure_count": 1,
                "repeat_failure_count": 1,
                "rca_completed_count": 3,
                "rca_pending_count": 1,
                "caused_shutdown_count": 2,
                "safety_incident_count": 1,
                "total_downtime_minutes": 360,
                "intervals_in_hours": [24, 48],
                "top_failure_modes": [
                    {"id": uuid4(), "name": "Bearing Failure", "failure_count": 2},
                ],
                "top_root_causes": [
                    {"id": uuid4(), "name": "Poor Lubrication", "failure_count": 2},
                ],
                "top_assets": [
                    {
                        "asset_id": uuid4(),
                        "asset_code": "AST-001",
                        "asset_name": "Pompa Utility",
                        "failure_count": 2,
                    }
                ],
            }
        ),
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


@pytest.mark.asyncio
async def test_get_sla_report_calculates_compliance(service: MaintenanceService) -> None:
    item = await service.get_sla_report()

    assert item.response_sla_compliance_pct == 80
    assert item.resolution_sla_compliance_pct == 50
    service.reports.get_sla_summary.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_reliability_report_calculates_metrics(
    service: MaintenanceService,
) -> None:
    item = await service.get_reliability_report()

    assert item.mttr_minutes == 150
    assert item.average_downtime_minutes == 80
    assert item.planned_vs_unplanned_ratio == 1
    assert item.repeat_failure_asset_count == 2


@pytest.mark.asyncio
async def test_get_failure_analysis_report_calculates_metrics(
    service: MaintenanceService,
) -> None:
    item = await service.get_failure_analysis_report(
        date_from=datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
        date_to=datetime(2026, 7, 27, 23, 59, tzinfo=UTC),
    )

    assert item.repeat_failure_rate_pct == 25
    assert item.rca_completion_rate_pct == 75
    assert item.average_downtime_minutes == 90
    assert item.mtbf_hours == 36
    assert item.open_failure_count == 1
    assert item.closed_failure_count == 1
    assert item.top_failure_modes[0].name == "Bearing Failure"

