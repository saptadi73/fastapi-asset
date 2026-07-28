from contextlib import asynccontextmanager
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.compat import UTC
from app.core.exceptions import AppError
from app.modules.maintenance.constants import MaintenanceScheduleStatus
from app.modules.maintenance.schemas import (
    MaintenanceScheduleConfirmPayload,
    MaintenanceScheduleReschedulePayload,
    MaintenanceTeamMemberCreate,
)
from app.modules.maintenance.service import MaintenanceService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> MaintenanceService:
    svc = MaintenanceService(FakeSession())
    svc.teams = SimpleNamespace(get=AsyncMock(), update=AsyncMock(), list=AsyncMock())
    svc.team_members = SimpleNamespace(create=AsyncMock())
    svc.schedules = SimpleNamespace(
        get=AsyncMock(),
        create=AsyncMock(),
        update=AsyncMock(),
        list=AsyncMock(),
        list_active_overlaps=AsyncMock(return_value=[]),
    )
    return svc


@pytest.mark.asyncio
async def test_add_team_member_rejects_invalid_period(service: MaintenanceService) -> None:
    team = SimpleNamespace(id=uuid4())
    service.get_team = AsyncMock(return_value=team)

    with pytest.raises(AppError) as exc_info:
        await service.add_team_member(
            team.id,
            MaintenanceTeamMemberCreate(
                employee_id=uuid4(),
                member_role="TECHNICIAN",
                effective_from=date(2026, 7, 27),
                effective_to=date(2026, 7, 26),
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_TEAM_MEMBER_PERIOD_INVALID"


@pytest.mark.asyncio
async def test_confirm_schedule_requires_planned_status(service: MaintenanceService) -> None:
    schedule = SimpleNamespace(id=uuid4(), status=MaintenanceScheduleStatus.CONFIRMED.value)
    service.get_schedule = AsyncMock(return_value=schedule)

    with pytest.raises(AppError) as exc_info:
        await service.confirm_schedule(
            schedule.id,
            MaintenanceScheduleConfirmPayload(actor_id=uuid4(), acted_at=datetime.now(UTC)),
        )

    assert exc_info.value.code == "MAINTENANCE_SCHEDULE_INVALID_STATUS"


@pytest.mark.asyncio
async def test_reschedule_rejects_overlap(service: MaintenanceService) -> None:
    schedule = SimpleNamespace(
        id=uuid4(),
        status=MaintenanceScheduleStatus.PLANNED.value,
        asset_id=uuid4(),
        maintenance_team_id=uuid4(),
        vendor_partner_id=None,
        reschedule_count=0,
    )
    service.get_schedule = AsyncMock(return_value=schedule)
    service.schedules.list_active_overlaps.return_value = [SimpleNamespace(id=uuid4())]

    with pytest.raises(AppError) as exc_info:
        await service.reschedule(
            schedule.id,
            MaintenanceScheduleReschedulePayload(
                actor_id=uuid4(),
                scheduled_start_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
                scheduled_end_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
                reschedule_reason="Bentrok tim",
            ),
        )

    assert exc_info.value.code == "MAINTENANCE_SCHEDULE_OVERLAP"

