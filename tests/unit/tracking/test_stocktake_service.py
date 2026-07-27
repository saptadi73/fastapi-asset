from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.modules.tracking.constants import StocktakeStatus
from app.modules.tracking.schemas import StocktakeActionPayload
from app.modules.tracking.service import AssetTrackingService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> AssetTrackingService:
    svc = AssetTrackingService(FakeSession())
    svc.stocktakes = SimpleNamespace(
        list=AsyncMock(),
        update=AsyncMock(),
    )
    svc.asset_lookup = SimpleNamespace(
        list_by_location=AsyncMock(),
    )
    svc.stocktake_expected_items = SimpleNamespace(
        create_many=AsyncMock(),
        list_by_session=AsyncMock(),
    )
    svc.stocktake_results = SimpleNamespace(
        create=AsyncMock(),
        list_by_session=AsyncMock(),
    )
    return svc


@pytest.mark.asyncio
async def test_start_stocktake_snapshots_assets_in_location(service: AssetTrackingService) -> None:
    session_id = uuid4()
    location_id = uuid4()
    asset = SimpleNamespace(
        id=uuid4(),
        current_primary_custodian_id=uuid4(),
    )
    stocktake = SimpleNamespace(
        id=session_id,
        location_id=location_id,
        status=StocktakeStatus.DRAFT.value,
        notes=None,
    )
    service.get_stocktake_session = AsyncMock(side_effect=[stocktake, stocktake])
    service.asset_lookup.list_by_location.return_value = [asset]

    payload = StocktakeActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC))

    result = await service.start_stocktake(session_id, payload)

    assert result is stocktake
    service.stocktakes.update.assert_awaited_once()
    service.stocktake_expected_items.create_many.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_stocktake_rejects_non_draft(service: AssetTrackingService) -> None:
    stocktake = SimpleNamespace(
        id=uuid4(),
        location_id=uuid4(),
        status=StocktakeStatus.IN_PROGRESS.value,
        notes=None,
    )
    service.get_stocktake_session = AsyncMock(return_value=stocktake)

    payload = StocktakeActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC))

    with pytest.raises(AppError) as exc_info:
        await service.start_stocktake(stocktake.id, payload)

    assert exc_info.value.code == "STOCKTAKE_SESSION_INVALID_STATUS"
    service.stocktakes.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_stocktake_creates_missing_for_unscanned_assets(
    service: AssetTrackingService,
) -> None:
    stocktake = SimpleNamespace(
        id=uuid4(),
        status=StocktakeStatus.IN_PROGRESS.value,
        notes=None,
    )
    expected_item = SimpleNamespace(asset_id=uuid4())
    service.get_stocktake_session = AsyncMock(side_effect=[stocktake, stocktake])
    service.stocktake_expected_items.list_by_session.return_value = [expected_item]
    service.stocktake_results.list_by_session.return_value = []

    payload = StocktakeActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC))

    result = await service.complete_stocktake(stocktake.id, payload)

    assert result is stocktake
    service.stocktake_results.create.assert_awaited_once()
    service.stocktakes.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_stocktake_rejects_non_completed(service: AssetTrackingService) -> None:
    stocktake = SimpleNamespace(
        id=uuid4(),
        status=StocktakeStatus.IN_PROGRESS.value,
        notes=None,
    )
    service.get_stocktake_session = AsyncMock(return_value=stocktake)

    payload = StocktakeActionPayload(actor_id=uuid4(), acted_at=datetime.now(UTC))

    with pytest.raises(AppError) as exc_info:
        await service.approve_stocktake(stocktake.id, payload)

    assert exc_info.value.code == "STOCKTAKE_SESSION_INVALID_STATUS"
    service.stocktakes.update.assert_not_awaited()
