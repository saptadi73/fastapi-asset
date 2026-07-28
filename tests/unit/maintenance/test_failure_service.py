from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.compat import UTC
from app.modules.maintenance.constants import (
    MaintenanceFailureSeverity,
    MaintenanceFailureStatus,
    MaintenanceWorkOrderEventType,
    MaintenanceWorkOrderStatus,
)
from app.modules.maintenance.schemas import AssetFailureCreate, AssetFailureUpdate
from app.modules.maintenance.service import MaintenanceService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield

    async def flush(self) -> None:
        return None

    async def refresh(self, *_args, **_kwargs) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.failures = SimpleNamespace(
        create=AsyncMock(),
        get=AsyncMock(),
        list=AsyncMock(return_value=([], 0)),
        update=AsyncMock(),
    )
    svc.events = SimpleNamespace(
        create=AsyncMock(),
        list_by_work_order=AsyncMock(return_value=[]),
    )
    svc.failure_modes = SimpleNamespace(get=AsyncMock())
    svc.symptom_codes = SimpleNamespace(get=AsyncMock())
    svc.root_cause_codes = SimpleNamespace(get=AsyncMock())
    return svc


@pytest.mark.asyncio
async def test_create_failure_records_event_and_auto_duration(
    service: MaintenanceService,
) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        requests=[],
    )
    refreshed = SimpleNamespace(id=work_order.id)
    service.get_work_order = AsyncMock(side_effect=[work_order, refreshed])

    result = await service.create_failure(
        work_order.id,
        AssetFailureCreate(
            failure_number="FLR-2026-0001",
            detected_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
            failure_description="Bearing motor macet dan menimbulkan getaran berat.",
            failure_severity=MaintenanceFailureSeverity.HIGH,
            caused_shutdown=True,
            failure_started_at=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
            failure_ended_at=datetime(2026, 7, 27, 10, 30, tzinfo=UTC),
            status=MaintenanceFailureStatus.RESOLVED,
            created_by=uuid4(),
        ),
    )

    assert result is refreshed
    service.failures.create.assert_awaited_once()
    created_failure = service.failures.create.await_args.args[0]
    assert created_failure.asset_id == work_order.asset_id
    assert created_failure.downtime_minutes == 150
    assert created_failure.status == MaintenanceFailureStatus.RESOLVED.value
    service.events.create.assert_awaited_once()
    created_event = service.events.create.await_args.args[0]
    assert created_event.event_type == MaintenanceWorkOrderEventType.FAILURE_RECORDED.value


@pytest.mark.asyncio
async def test_create_failure_rejects_invalid_failure_period(
    service: MaintenanceService,
) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        requests=[],
    )
    service.get_work_order = AsyncMock(return_value=work_order)

    with pytest.raises(Exception) as exc_info:
        await service.create_failure(
            work_order.id,
            AssetFailureCreate(
                failure_number="FLR-2026-0002",
                detected_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
                failure_description="Sensor trip palsu.",
                failure_severity=MaintenanceFailureSeverity.MEDIUM,
                failure_started_at=datetime(2026, 7, 27, 11, 0, tzinfo=UTC),
                failure_ended_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
                created_by=uuid4(),
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_ASSET_FAILURE_TIME_INVALID"


@pytest.mark.asyncio
async def test_update_failure_finalizes_rca_and_auto_duration(
    service: MaintenanceService,
) -> None:
    failure = SimpleNamespace(
        id=uuid4(),
        failure_number="FLR-2026-0003",
        work_order_id=uuid4(),
        detected_by_employee_id=uuid4(),
        failure_started_at=datetime(2026, 7, 27, 7, 0, tzinfo=UTC),
        failure_ended_at=None,
        downtime_minutes=None,
        status=MaintenanceFailureStatus.OPEN.value,
        repeat_failure=False,
        caused_shutdown=True,
    )
    updated_failure = SimpleNamespace(id=failure.id, status=MaintenanceFailureStatus.CLOSED.value)
    actor_id = uuid4()
    root_cause_code_id = uuid4()

    service.failures.get = AsyncMock(side_effect=[failure, updated_failure])
    service.root_cause_codes.get = AsyncMock(return_value=SimpleNamespace(id=root_cause_code_id))

    result = await service.update_failure(
        failure.id,
        AssetFailureUpdate(
            root_cause_code_id=root_cause_code_id,
            root_cause_description="Analisis menunjukkan misalignment coupling.",
            corrective_action="Realignment dan pengencangan ulang.",
            preventive_action="Tambahkan inspeksi alignment mingguan.",
            failure_ended_at=datetime(2026, 7, 27, 9, 30, tzinfo=UTC),
            status=MaintenanceFailureStatus.CLOSED,
        ),
        actor_id=actor_id,
    )

    assert result is updated_failure
    service.failures.update.assert_awaited_once()
    update_changes = service.failures.update.await_args.kwargs
    assert update_changes["status"] == MaintenanceFailureStatus.CLOSED.value
    assert update_changes["downtime_minutes"] == 150
    service.events.create.assert_awaited_once()
    created_event = service.events.create.await_args.args[0]
    assert created_event.event_type == MaintenanceWorkOrderEventType.RCA_FINALIZED.value


@pytest.mark.asyncio
async def test_update_failure_rejects_invalid_failure_period(
    service: MaintenanceService,
) -> None:
    failure = SimpleNamespace(
        id=uuid4(),
        failure_number="FLR-2026-0004",
        work_order_id=uuid4(),
        detected_by_employee_id=uuid4(),
        failure_started_at=datetime(2026, 7, 27, 12, 0, tzinfo=UTC),
        failure_ended_at=None,
        downtime_minutes=None,
        status=MaintenanceFailureStatus.OPEN.value,
        repeat_failure=False,
        caused_shutdown=False,
    )
    service.failures.get = AsyncMock(return_value=failure)

    with pytest.raises(Exception) as exc_info:
        await service.update_failure(
            failure.id,
            AssetFailureUpdate(
                failure_ended_at=datetime(2026, 7, 27, 11, 0, tzinfo=UTC),
            ),
            actor_id=uuid4(),
        )

    assert exc_info.value.code == "MAINTENANCE_ASSET_FAILURE_TIME_INVALID"

