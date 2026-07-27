from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.modules.assets.constants import AssetTransferStatus
from app.modules.assets.schemas import AssetTransferActionPayload
from app.modules.assets.service import AssetRegistryService
from app.shared.pagination import PaginationParams


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield


@pytest.fixture
def service() -> AssetRegistryService:
    svc = AssetRegistryService(FakeSession())
    svc.transfers = SimpleNamespace(
        list=AsyncMock(),
        update=AsyncMock(),
    )
    svc.assets = SimpleNamespace(
        get_for_update=AsyncMock(),
        update=AsyncMock(),
    )
    svc.location_histories = SimpleNamespace(
        get_active=AsyncMock(),
        close_active=AsyncMock(),
        create=AsyncMock(),
    )
    svc.assignments = SimpleNamespace(
        get_active_primary_custodian=AsyncMock(),
        close_assignment=AsyncMock(),
        create=AsyncMock(),
    )
    return svc


@pytest.mark.asyncio
async def test_list_transfers_forwards_filters(service: AssetRegistryService) -> None:
    pagination = PaginationParams(page=1, page_size=20, search="TRF")
    transfer = SimpleNamespace(id=uuid4())
    service.transfers.list.return_value = ([transfer], 1)

    items, total_items = await service.list_transfers(
        pagination,
        status_filter="APPROVED",
        requested_by=uuid4(),
    )

    assert items == [transfer]
    assert total_items == 1
    service.transfers.list.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_transfer_updates_status_from_draft(service: AssetRegistryService) -> None:
    transfer_id = uuid4()
    actor_id = uuid4()
    transfer = SimpleNamespace(
        id=transfer_id,
        status=AssetTransferStatus.DRAFT.value,
        requested_by=None,
    )
    service.get_transfer = AsyncMock(side_effect=[transfer, transfer])

    payload = AssetTransferActionPayload(
        actor_id=actor_id,
        acted_at=datetime.now(UTC),
    )

    result = await service.submit_transfer(transfer_id, payload)

    assert result is transfer
    service.transfers.update.assert_awaited_once_with(
        transfer,
        status=AssetTransferStatus.SUBMITTED.value,
        requested_by=actor_id,
    )


@pytest.mark.asyncio
async def test_submit_transfer_rejects_non_draft(service: AssetRegistryService) -> None:
    transfer_id = uuid4()
    transfer = SimpleNamespace(
        id=transfer_id,
        status=AssetTransferStatus.APPROVED.value,
        requested_by=None,
    )
    service.get_transfer = AsyncMock(return_value=transfer)

    payload = AssetTransferActionPayload(
        actor_id=uuid4(),
        acted_at=datetime.now(UTC),
    )

    with pytest.raises(AppError) as exc_info:
        await service.submit_transfer(transfer_id, payload)

    assert exc_info.value.code == "ASSET_TRANSFER_INVALID_STATUS"
    service.transfers.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_transfer_rejects_source_location_mismatch(
    service: AssetRegistryService,
) -> None:
    transfer_id = uuid4()
    transfer = SimpleNamespace(
        id=transfer_id,
        status=AssetTransferStatus.APPROVED.value,
        from_location_id=uuid4(),
        to_location_id=uuid4(),
        transfer_number="TRF-001",
        reason="Move asset",
        items=[
            SimpleNamespace(
                asset_id=uuid4(),
                new_custodian_id=None,
                item_status="PENDING",
            )
        ],
    )
    locked_asset = SimpleNamespace(
        id=transfer.items[0].asset_id,
        current_location_id=uuid4(),
        current_primary_custodian_id=None,
    )
    service.get_transfer = AsyncMock(return_value=transfer)
    service.assets.get_for_update.return_value = locked_asset

    payload = AssetTransferActionPayload(
        actor_id=uuid4(),
        acted_at=datetime.now(UTC),
    )

    with pytest.raises(AppError) as exc_info:
        await service.complete_transfer(transfer_id, payload)

    assert exc_info.value.code == "ASSET_TRANSFER_SOURCE_LOCATION_MISMATCH"
    service.location_histories.create.assert_not_awaited()
    service.assets.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_transfer_updates_histories_and_assignment(
    service: AssetRegistryService,
) -> None:
    transfer_id = uuid4()
    from_location_id = uuid4()
    to_location_id = uuid4()
    previous_custodian_id = uuid4()
    new_custodian_id = uuid4()
    asset_id = uuid4()
    acted_at = datetime.now(UTC)
    actor_id = uuid4()

    transfer_item = SimpleNamespace(
        asset_id=asset_id,
        new_custodian_id=new_custodian_id,
        item_status="PENDING",
    )
    transfer = SimpleNamespace(
        id=transfer_id,
        status=AssetTransferStatus.APPROVED.value,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        transfer_number="TRF-002",
        reason="Relocate for operations",
        items=[transfer_item],
    )
    locked_asset = SimpleNamespace(
        id=asset_id,
        current_location_id=from_location_id,
        current_primary_custodian_id=previous_custodian_id,
    )
    active_location_history = SimpleNamespace(id=uuid4())
    active_assignment = SimpleNamespace(id=uuid4())

    service.get_transfer = AsyncMock(side_effect=[transfer, transfer])
    service.assets.get_for_update.return_value = locked_asset
    service.location_histories.get_active.return_value = active_location_history
    service.assignments.get_active_primary_custodian.return_value = active_assignment

    payload = AssetTransferActionPayload(actor_id=actor_id, acted_at=acted_at)

    result = await service.complete_transfer(transfer_id, payload)

    assert result is transfer
    service.location_histories.close_active.assert_awaited_once_with(
        active_location_history,
        ended_at=acted_at,
    )
    service.location_histories.create.assert_awaited()
    service.assignments.close_assignment.assert_awaited_once_with(
        active_assignment,
        returned_at=acted_at,
    )
    service.assignments.create.assert_awaited()
    service.assets.update.assert_any_await(
        locked_asset,
        current_location_id=to_location_id,
        current_primary_custodian_id=new_custodian_id,
    )
    service.transfers.update.assert_awaited_once()
    assert transfer_item.item_status == "COMPLETED"
