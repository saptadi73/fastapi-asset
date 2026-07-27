from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.modules.maintenance.constants import (
    MaintenanceRequestStatus,
    MaintenanceWorkOrderStatus,
)
from app.modules.maintenance.schemas import (
    MaintenanceConvertToWorkOrderPayload,
    MaintenanceRequestActionPayload,
    MaintenanceRequestRejectPayload,
    MaintenanceWorkOrderCompletePayload,
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
    svc.work_orders = SimpleNamespace(create=AsyncMock(), update=AsyncMock())
    svc.request_work_orders = SimpleNamespace(create=AsyncMock())
    svc.checklist_executions = SimpleNamespace(list_by_work_order=AsyncMock(return_value=[]))
    svc.findings = SimpleNamespace(list_by_work_order=AsyncMock(return_value=[]))
    svc.part_usages = SimpleNamespace(list_by_work_order=AsyncMock(return_value=[]))
    svc.labor_logs = SimpleNamespace(list_by_work_order=AsyncMock(return_value=[]))
    svc.assets = SimpleNamespace(get=AsyncMock(), update=AsyncMock())
    svc.priorities = SimpleNamespace(get=AsyncMock())
    svc.partners = SimpleNamespace(get=AsyncMock())
    svc.asset_status_histories = SimpleNamespace(create=AsyncMock())
    return svc


@pytest.mark.asyncio
async def test_submit_request_rejects_non_draft(service: MaintenanceService) -> None:
    request = SimpleNamespace(id=uuid4(), status=MaintenanceRequestStatus.APPROVED.value)
    service.get_request = AsyncMock(return_value=request)

    with pytest.raises(AppError) as exc_info:
        await service.submit_request(
            request.id,
            MaintenanceRequestActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC)),
        )

    assert exc_info.value.code == "MAINTENANCE_REQUEST_INVALID_STATUS"
    service.requests.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_reject_request_updates_reason(service: MaintenanceService) -> None:
    request = SimpleNamespace(id=uuid4(), status=MaintenanceRequestStatus.TRIAGE.value)
    service.get_request = AsyncMock(side_effect=[request, request])

    result = await service.reject_request(
        request.id,
        MaintenanceRequestRejectPayload(
            actor_id=uuid4(),
            acted_at=datetime.now(UTC),
            rejection_reason="Informasi tidak cukup",
        ),
    )

    assert result is request
    service.requests.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_convert_request_to_work_order_updates_request_status(
    service: MaintenanceService,
) -> None:
    asset_id = uuid4()
    priority_id = uuid4()
    request = SimpleNamespace(
        id=uuid4(),
        status=MaintenanceRequestStatus.APPROVED.value,
        company_id=uuid4(),
        asset_id=asset_id,
        priority_id=priority_id,
        title="Motor panas",
    )
    created_work_order = SimpleNamespace(id=uuid4())
    service.get_request = AsyncMock(return_value=request)
    service.get_work_order = AsyncMock(return_value=created_work_order)
    service.assets.get.return_value = SimpleNamespace(id=asset_id, condition_status="GOOD")
    service.priorities.get.return_value = SimpleNamespace(id=priority_id)
    service.work_orders.create.return_value = created_work_order

    payload = MaintenanceConvertToWorkOrderPayload(
        work_order_number="WO-001",
        maintenance_type="CORRECTIVE",
        execution_mode="INTERNAL",
        scope_of_work="Diagnosa dan perbaikan",
        created_by=uuid4(),
    )

    result = await service.convert_request_to_work_order(request.id, payload)

    assert result is created_work_order
    service.requests.update.assert_awaited_once()
    kwargs = service.requests.update.await_args.kwargs
    assert kwargs["status"] == MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER.value


@pytest.mark.asyncio
async def test_complete_work_order_rejects_invalid_end_time(service: MaintenanceService) -> None:
    started_at = datetime(2026, 7, 27, 10, 0, tzinfo=UTC)
    work_order = SimpleNamespace(
        id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        actual_start_at=started_at,
    )
    service.get_work_order = AsyncMock(return_value=work_order)

    with pytest.raises(AppError) as exc_info:
        await service.complete_work_order(
            work_order.id,
            MaintenanceWorkOrderCompletePayload(
                actor_id=uuid4(),
                acted_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
                completion_summary="Selesai",
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_WORK_ORDER_TIME_INVALID"
