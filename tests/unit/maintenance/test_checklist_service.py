from contextlib import asynccontextmanager
from datetime import UTC, datetime
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
    MaintenanceChecklistExecutionStartPayload,
    MaintenanceChecklistResultSubmitPayload,
    MaintenanceFindingCreateRequestPayload,
)
from app.modules.maintenance.service import MaintenanceService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.work_orders = SimpleNamespace(
        create=AsyncMock(),
        update=AsyncMock(),
        get=AsyncMock(),
        list_by_asset=AsyncMock(return_value=[]),
    )
    svc.plans = SimpleNamespace(create=AsyncMock(), get=AsyncMock(), update=AsyncMock())
    svc.checklist_templates = SimpleNamespace(create=AsyncMock(), get=AsyncMock())
    svc.checklist_template_items = SimpleNamespace(create=AsyncMock())
    svc.checklist_executions = SimpleNamespace(
        create=AsyncMock(),
        get=AsyncMock(),
        update=AsyncMock(),
    )
    svc.checklist_results = SimpleNamespace(create=AsyncMock())
    svc.findings = SimpleNamespace(create=AsyncMock(), get=AsyncMock(), update=AsyncMock())
    svc.requests = SimpleNamespace(create=AsyncMock(), update=AsyncMock())
    svc.assets = SimpleNamespace(get=AsyncMock())
    svc.priorities = SimpleNamespace(get=AsyncMock())
    svc.partners = SimpleNamespace(get=AsyncMock())
    return svc


@pytest.mark.asyncio
async def test_start_work_order_checklist_requires_template(
    service: MaintenanceService,
) -> None:
    work_order = SimpleNamespace(
        id=uuid4(),
        asset_id=uuid4(),
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
        maintenance_plan_id=None,
    )
    service.get_work_order = AsyncMock(return_value=work_order)

    with pytest.raises(AppError) as exc_info:
        await service.start_work_order_checklist(
            work_order.id,
            MaintenanceChecklistExecutionStartPayload(
                performed_by_employee_id=uuid4(),
                started_at=datetime.now(UTC),
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_CHECKLIST_TEMPLATE_REQUIRED"


@pytest.mark.asyncio
async def test_submit_checklist_results_creates_finding_and_completes_execution(
    service: MaintenanceService,
) -> None:
    template_item = SimpleNamespace(
        id=uuid4(),
        item_code="TEMP-001",
        response_type="NUMERIC",
        is_required=True,
        normal_min_value=10,
        normal_max_value=20,
        failure_response_rule="REQUIRES_FOLLOW_UP",
    )
    execution = SimpleNamespace(
        id=uuid4(),
        status=ChecklistExecutionStatus.IN_PROGRESS.value,
        work_order_id=uuid4(),
        asset_id=uuid4(),
        performed_by_employee_id=uuid4(),
        template=SimpleNamespace(items=[template_item]),
    )
    work_order = SimpleNamespace(
        id=execution.work_order_id,
        status=MaintenanceWorkOrderStatus.IN_PROGRESS.value,
    )
    created_result = SimpleNamespace(id=uuid4())
    refreshed_execution = SimpleNamespace(
        id=execution.id,
        status=ChecklistExecutionStatus.COMPLETED.value,
        overall_result="FAIL",
    )

    service.get_checklist_execution = AsyncMock(side_effect=[execution, refreshed_execution])
    service.get_work_order = AsyncMock(return_value=work_order)
    service.checklist_results.create.return_value = created_result

    result = await service.submit_checklist_results(
        execution.id,
        MaintenanceChecklistResultSubmitPayload(
            completed_at=datetime(2026, 7, 27, 11, 0, tzinfo=UTC),
            results=[
                {
                    "template_item_id": template_item.id,
                    "numeric_value": 25,
                    "performed_at": datetime(2026, 7, 27, 10, 30, tzinfo=UTC),
                }
            ],
        ),
    )

    assert result is refreshed_execution
    service.findings.create.assert_awaited_once()
    service.checklist_executions.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_request_from_finding_rejects_duplicate_request(
    service: MaintenanceService,
) -> None:
    finding = SimpleNamespace(
        id=uuid4(),
        generated_request_id=uuid4(),
        asset=SimpleNamespace(company_id=uuid4(), current_location_id=uuid4()),
        asset_id=uuid4(),
        reported_by_employee_id=uuid4(),
        requires_asset_shutdown=False,
        finding_type="DEFECT",
        work_order=None,
    )
    service.get_finding = AsyncMock(return_value=finding)

    with pytest.raises(AppError) as exc_info:
        await service.create_request_from_finding(
            finding.id,
            MaintenanceFindingCreateRequestPayload(
                request_number="MR-001",
                priority_id=uuid4(),
                reported_at=datetime.now(UTC),
                title="Follow up finding",
                problem_description="Perlu tindakan lanjutan",
                created_by=uuid4(),
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_FINDING_REQUEST_CONFLICT"


@pytest.mark.asyncio
async def test_create_request_from_finding_updates_finding(
    service: MaintenanceService,
) -> None:
    finding = SimpleNamespace(
        id=uuid4(),
        generated_request_id=None,
        asset=SimpleNamespace(company_id=uuid4(), current_location_id=uuid4()),
        asset_id=uuid4(),
        reported_by_employee_id=uuid4(),
        requires_asset_shutdown=True,
        finding_type="SAFETY_RISK",
        work_order=SimpleNamespace(requests=[]),
    )
    created_request = SimpleNamespace(id=uuid4())
    service.get_finding = AsyncMock(return_value=finding)
    service.get_request = AsyncMock(return_value=created_request)
    service.priorities.get.return_value = SimpleNamespace(id=uuid4())
    service.requests.create.side_effect = lambda item: setattr(created_request, "id", item.id)

    result = await service.create_request_from_finding(
        finding.id,
        MaintenanceFindingCreateRequestPayload(
            request_number="MR-002",
            priority_id=uuid4(),
            reported_at=datetime(2026, 7, 27, 12, 0, tzinfo=UTC),
            title="Tindak lanjut finding safety",
            problem_description="Temuan perlu request baru",
            created_by=uuid4(),
            submit=True,
        ),
    )

    assert result is created_request
    service.findings.update.assert_awaited_once()
    assert (
        service.findings.update.await_args.kwargs["status"]
        == MaintenanceFindingStatus.FOLLOW_UP_CREATED.value
    )
