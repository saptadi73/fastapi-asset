from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.assets.constants import (
    AssetAttributeDataType,
    AssetOwnerType,
    AssetTimelineEventType,
    AssetTransferItemStatus,
    AssetTransferStatus,
    AssignmentType,
)
from app.modules.assets.exceptions import (
    AssetAttributeDefinitionNotFoundError,
    AssetCategoryNotFoundError,
    AssetClassNotFoundError,
    AssetLocationNotFoundError,
    AssetNotFoundError,
    AssetTransferNotFoundError,
)
from app.modules.assets.models import (
    Asset,
    AssetAssignment,
    AssetAttributeDefinition,
    AssetAttributeValue,
    AssetCategory,
    AssetClass,
    AssetLocation,
    AssetLocationHistory,
    AssetOwnership,
    AssetStatusHistory,
    AssetTransfer,
    AssetTransferItem,
)
from app.modules.assets.repository import (
    AssetAssignmentRepository,
    AssetAttributeDefinitionRepository,
    AssetAttributeValueRepository,
    AssetCategoryRepository,
    AssetClassRepository,
    AssetLocationHistoryRepository,
    AssetLocationRepository,
    AssetOwnershipRepository,
    AssetRepository,
    AssetStatusHistoryRepository,
    AssetTransferItemRepository,
    AssetTransferRepository,
)
from app.modules.assets.schemas import (
    AssetAssignmentCreate,
    AssetAttributeDefinitionCreate,
    AssetAttributeValueCreate,
    AssetCategoryCreate,
    AssetClassCreate,
    AssetCreate,
    AssetLocationChangeCreate,
    AssetLocationCreate,
    AssetOwnershipCreate,
    AssetStatusChangeCreate,
    AssetTimelineEventRead,
    AssetTransferActionPayload,
    AssetTransferCreate,
    AssetUpdate,
)
from app.shared.pagination import PaginationParams


class AssetRegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.asset_categories = AssetCategoryRepository(session)
        self.asset_classes = AssetClassRepository(session)
        self.locations = AssetLocationRepository(session)
        self.attribute_definitions = AssetAttributeDefinitionRepository(session)
        self.attribute_values = AssetAttributeValueRepository(session)
        self.ownerships = AssetOwnershipRepository(session)
        self.assets = AssetRepository(session)
        self.location_histories = AssetLocationHistoryRepository(session)
        self.assignments = AssetAssignmentRepository(session)
        self.status_histories = AssetStatusHistoryRepository(session)
        self.transfers = AssetTransferRepository(session)
        self.transfer_items = AssetTransferItemRepository(session)

    async def create_category(self, payload: AssetCategoryCreate) -> AssetCategory:
        if payload.parent_category_id:
            parent = await self.asset_categories.get(payload.parent_category_id)
            if parent is None:
                raise AssetCategoryNotFoundError(str(payload.parent_category_id))

        category = AssetCategory(**payload.model_dump())
        try:
            async with self.session.begin():
                return await self.asset_categories.create(category)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_CATEGORY_CONFLICT",
                message="Category code sudah digunakan.",
                status_code=409,
            ) from exc

    async def list_categories(self) -> list[AssetCategory]:
        items = await self.asset_categories.list()
        return list(items)

    async def create_class(self, payload: AssetClassCreate) -> AssetClass:
        asset_class = AssetClass(**payload.model_dump())
        try:
            async with self.session.begin():
                return await self.asset_classes.create(asset_class)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_CLASS_CONFLICT",
                message="Class code sudah digunakan.",
                status_code=409,
            ) from exc

    async def list_classes(self) -> list[AssetClass]:
        items = await self.asset_classes.list()
        return list(items)

    async def create_location(self, payload: AssetLocationCreate) -> AssetLocation:
        if payload.parent_location_id:
            parent = await self.locations.get(payload.parent_location_id)
            if parent is None:
                raise AssetLocationNotFoundError(str(payload.parent_location_id))

        location = AssetLocation(**payload.model_dump(mode="python"))
        try:
            async with self.session.begin():
                return await self.locations.create(location)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_LOCATION_CONFLICT",
                message="Location code sudah digunakan.",
                status_code=409,
            ) from exc

    async def list_locations(self) -> list[AssetLocation]:
        items = await self.locations.list()
        return list(items)

    async def create_attribute_definition(
        self,
        payload: AssetAttributeDefinitionCreate,
    ) -> AssetAttributeDefinition:
        category = await self.asset_categories.get(payload.asset_category_id)
        if category is None:
            raise AssetCategoryNotFoundError(str(payload.asset_category_id))

        definition = AssetAttributeDefinition(
            **payload.model_dump(mode="python"),
            data_type=payload.data_type.value,
        )
        try:
            async with self.session.begin():
                return await self.attribute_definitions.create(definition)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_ATTRIBUTE_DEFINITION_CONFLICT",
                message="Attribute code sudah digunakan pada kategori ini.",
                status_code=409,
            ) from exc

    async def list_attribute_definitions(
        self,
        asset_category_id: UUID,
    ) -> list[AssetAttributeDefinition]:
        category = await self.asset_categories.get(asset_category_id)
        if category is None:
            raise AssetCategoryNotFoundError(str(asset_category_id))
        items = await self.attribute_definitions.list_by_category(asset_category_id)
        return list(items)

    async def create_asset(self, payload: AssetCreate) -> Asset:
        await self._validate_asset_relations(
            payload.asset_category_id,
            payload.asset_class_id,
            payload.parent_asset_id,
        )

        asset = Asset(
            **payload.model_dump(mode="python"),
            asset_type=payload.asset_type.value,
            asset_status=payload.asset_status.value,
            condition_status=payload.condition_status.value,
        )
        try:
            async with self.session.begin():
                return await self.assets.create(asset)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_CONFLICT",
                message="Asset code sudah digunakan atau relasi tidak valid.",
                status_code=409,
            ) from exc

    async def list_assets(self, pagination: PaginationParams) -> tuple[list[Asset], int]:
        items, total_items = await self.assets.list(pagination)
        return list(items), total_items

    async def get_asset(self, asset_id: UUID) -> Asset:
        asset = await self.assets.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))
        return asset

    async def update_asset(self, asset_id: UUID, payload: AssetUpdate) -> Asset:
        asset = await self.get_asset(asset_id)

        if payload.asset_class_id is not None:
            asset_class = await self.asset_classes.get(payload.asset_class_id)
            if asset_class is None:
                raise AssetClassNotFoundError(str(payload.asset_class_id))

        if payload.parent_asset_id is not None:
            parent = await self.assets.get(payload.parent_asset_id)
            if parent is None:
                raise AssetNotFoundError(str(payload.parent_asset_id))
            if parent.id == asset.id:
                raise AppError(
                    code="ASSET_PARENT_INVALID",
                    message="Asset tidak boleh menjadi parent dirinya sendiri.",
                    status_code=409,
                )

        changes = payload.model_dump(exclude_unset=True, mode="python")
        if payload.asset_status is not None:
            changes["asset_status"] = payload.asset_status.value
        if payload.condition_status is not None:
            changes["condition_status"] = payload.condition_status.value

        try:
            async with self.session.begin():
                return await self.assets.update(asset, **changes)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_UPDATE_CONFLICT",
                message="Perubahan asset menimbulkan konflik data.",
                status_code=409,
            ) from exc

    async def upsert_attribute_value(
        self,
        asset_id: UUID,
        payload: AssetAttributeValueCreate,
    ) -> AssetAttributeValue:
        asset = await self.get_asset(asset_id)
        definition = await self.attribute_definitions.get(payload.attribute_definition_id)
        if definition is None:
            raise AssetAttributeDefinitionNotFoundError(str(payload.attribute_definition_id))

        if definition.asset_category_id != asset.asset_category_id:
            raise AppError(
                code="ASSET_ATTRIBUTE_CATEGORY_MISMATCH",
                message="Attribute definition tidak cocok dengan kategori asset.",
                status_code=409,
            )

        self._validate_attribute_value(definition.data_type, payload)

        existing = await self.attribute_values.get_by_asset_and_definition(
            asset_id=asset.id,
            definition_id=definition.id,
        )
        new_value = AssetAttributeValue(
            asset_id=asset.id,
            attribute_definition_id=definition.id,
            value_text=payload.value_text,
            value_number=payload.value_number,
            value_date=payload.value_date,
            value_boolean=payload.value_boolean,
            value_json=payload.value_json,
        )

        async with self.session.begin():
            await self.attribute_values.upsert(existing=existing, new_value=new_value)
            await self.assets.update(asset, updated_by=asset.updated_by)

        values = await self.attribute_values.list_by_asset(asset_id)
        return next(item for item in values if item.attribute_definition_id == definition.id)

    async def list_attribute_values(self, asset_id: UUID) -> list[AssetAttributeValue]:
        await self.get_asset(asset_id)
        items = await self.attribute_values.list_by_asset(asset_id)
        return list(items)

    async def create_ownership(
        self,
        asset_id: UUID,
        payload: AssetOwnershipCreate,
    ) -> AssetOwnership:
        asset = await self.get_asset(asset_id)
        self._validate_ownership_payload(payload)

        ownership = AssetOwnership(
            asset_id=asset.id,
            owner_type=payload.owner_type.value,
            owner_partner_id=payload.owner_partner_id,
            owner_company_id=payload.owner_company_id,
            ownership_percentage=payload.ownership_percentage,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            source_reference=payload.source_reference,
            notes=payload.notes,
        )

        existing_ownerships = await self.ownerships.list_by_asset(asset_id)
        self._validate_ownership_overlap(existing_ownerships, ownership)

        async with self.session.begin():
            await self.ownerships.create(ownership)

        items = await self.ownerships.list_by_asset(asset_id)
        return items[0]

    async def list_ownerships(self, asset_id: UUID) -> list[AssetOwnership]:
        await self.get_asset(asset_id)
        items = await self.ownerships.list_by_asset(asset_id)
        return list(items)

    async def create_transfer(self, payload: AssetTransferCreate) -> AssetTransfer:
        to_location = await self.locations.get(payload.to_location_id)
        if to_location is None:
            raise AssetLocationNotFoundError(str(payload.to_location_id))

        if payload.from_location_id is not None:
            from_location = await self.locations.get(payload.from_location_id)
            if from_location is None:
                raise AssetLocationNotFoundError(str(payload.from_location_id))

        if not payload.items:
            raise AppError(
                code="ASSET_TRANSFER_ITEMS_REQUIRED",
                message="Transfer harus memiliki minimal satu item asset.",
                status_code=422,
            )

        transfer = AssetTransfer(
            transfer_number=payload.transfer_number,
            transfer_date=payload.transfer_date,
            transfer_type=payload.transfer_type.value,
            status=AssetTransferStatus.DRAFT.value,
            movement_purpose=payload.movement_purpose,
            is_permanent=payload.is_permanent,
            expected_return_at=payload.expected_return_at,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id,
            from_department_id=payload.from_department_id,
            to_department_id=payload.to_department_id,
            requested_by=payload.requested_by,
            reason=payload.reason,
        )
        items = [
            AssetTransferItem(
                asset_id=item.asset_id,
                previous_custodian_id=item.previous_custodian_id,
                new_custodian_id=item.new_custodian_id,
                handover_condition=item.handover_condition,
                dispatch_scan_event_id=item.dispatch_scan_event_id,
                receipt_scan_event_id=item.receipt_scan_event_id,
                item_status=item.item_status.value,
                notes=item.notes,
            )
            for item in payload.items
        ]

        try:
            async with self.session.begin():
                created_transfer = await self.transfers.create(transfer)
                for item in items:
                    item.asset_transfer_id = created_transfer.id
                await self.transfer_items.create_many(items)
        except IntegrityError as exc:
            raise AppError(
                code="ASSET_TRANSFER_CONFLICT",
                message="Transfer number sudah digunakan atau item asset duplikat.",
                status_code=409,
            ) from exc

        result = await self.get_transfer(created_transfer.id)
        return result

    async def get_transfer(self, transfer_id: UUID) -> AssetTransfer:
        transfer = await self.transfers.get(transfer_id)
        if transfer is None:
            raise AssetTransferNotFoundError(str(transfer_id))
        return transfer

    async def list_transfers(
        self,
        pagination: PaginationParams,
        *,
        status_filter: str | None = None,
        to_location_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> tuple[list[AssetTransfer], int]:
        items, total_items = await self.transfers.list(
            pagination,
            status_filter=status_filter,
            to_location_id=to_location_id,
            requested_by=requested_by,
        )
        return list(items), total_items

    async def submit_transfer(
        self,
        transfer_id: UUID,
        payload: AssetTransferActionPayload,
    ) -> AssetTransfer:
        transfer = await self.get_transfer(transfer_id)
        if transfer.status != AssetTransferStatus.DRAFT.value:
            raise AppError(
                code="ASSET_TRANSFER_INVALID_STATUS",
                message="Hanya transfer DRAFT yang dapat disubmit.",
                status_code=409,
            )

        async with self.session.begin():
            await self.transfers.update(
                transfer,
                status=AssetTransferStatus.SUBMITTED.value,
                requested_by=payload.actor_id or transfer.requested_by,
            )
        return await self.get_transfer(transfer_id)

    async def approve_transfer(
        self,
        transfer_id: UUID,
        payload: AssetTransferActionPayload,
    ) -> AssetTransfer:
        transfer = await self.get_transfer(transfer_id)
        if transfer.status != AssetTransferStatus.SUBMITTED.value:
            raise AppError(
                code="ASSET_TRANSFER_INVALID_STATUS",
                message="Hanya transfer SUBMITTED yang dapat diapprove.",
                status_code=409,
            )

        async with self.session.begin():
            await self.transfers.update(
                transfer,
                status=AssetTransferStatus.APPROVED.value,
                approved_by=payload.actor_id,
                approved_at=payload.acted_at,
            )
        return await self.get_transfer(transfer_id)

    async def complete_transfer(
        self,
        transfer_id: UUID,
        payload: AssetTransferActionPayload,
    ) -> AssetTransfer:
        transfer = await self.get_transfer(transfer_id)
        if transfer.status != AssetTransferStatus.APPROVED.value:
            raise AppError(
                code="ASSET_TRANSFER_INVALID_STATUS",
                message="Hanya transfer APPROVED yang dapat diselesaikan.",
                status_code=409,
            )

        async with self.session.begin():
            locked_assets: list[Asset] = []
            for item in transfer.items:
                asset = await self.assets.get_for_update(item.asset_id)
                if asset is None:
                    raise AssetNotFoundError(str(item.asset_id))

                if (
                    transfer.from_location_id
                    and asset.current_location_id != transfer.from_location_id
                ):
                    raise AppError(
                        code="ASSET_TRANSFER_SOURCE_LOCATION_MISMATCH",
                        message="Lokasi asset tidak sesuai dengan lokasi asal transfer.",
                        status_code=409,
                        details={
                            "asset_id": str(asset.id),
                            "current_location_id": (
                                str(asset.current_location_id)
                                if asset.current_location_id
                                else None
                            ),
                            "expected_from_location_id": str(transfer.from_location_id),
                        },
                    )
                locked_assets.append(asset)

            for asset, item in zip(locked_assets, transfer.items, strict=False):
                active_history = await self.location_histories.get_active(asset.id)
                if active_history is not None:
                    await self.location_histories.close_active(
                        active_history,
                        ended_at=payload.acted_at,
                    )

                await self.location_histories.create(
                    AssetLocationHistory(
                        asset_id=asset.id,
                        from_location_id=asset.current_location_id,
                        to_location_id=transfer.to_location_id,
                        effective_at=payload.acted_at,
                        transfer_id=transfer.id,
                        reason=transfer.reason,
                        recorded_by=payload.actor_id,
                    )
                )

                if item.new_custodian_id is not None:
                    active_assignment = await self.assignments.get_active_primary_custodian(
                        asset.id
                    )
                    if active_assignment is not None:
                        await self.assignments.close_assignment(
                            active_assignment,
                            returned_at=payload.acted_at,
                        )

                    await self.assignments.create(
                        AssetAssignment(
                            asset_id=asset.id,
                            assignment_type=AssignmentType.PRIMARY_CUSTODIAN.value,
                            employee_id=item.new_custodian_id,
                            assigned_at=payload.acted_at,
                            assignment_status="ACTIVE",
                            notes=f"Transfer {transfer.transfer_number}",
                        )
                    )

                await self.assets.update(
                    asset,
                    current_location_id=transfer.to_location_id,
                    current_primary_custodian_id=item.new_custodian_id
                    if item.new_custodian_id is not None
                    else asset.current_primary_custodian_id,
                )
                item.item_status = AssetTransferItemStatus.COMPLETED.value

            await self.transfers.update(
                transfer,
                status=AssetTransferStatus.COMPLETED.value,
                dispatched_by=payload.actor_id,
                dispatched_at=payload.acted_at,
                received_by=payload.actor_id,
                received_at=payload.acted_at,
            )

        return await self.get_transfer(transfer_id)

    async def record_location_change(
        self,
        asset_id: UUID,
        payload: AssetLocationChangeCreate,
    ) -> AssetLocationHistory:
        asset = await self.get_asset(asset_id)
        to_location = await self.locations.get(payload.to_location_id)
        if to_location is None:
            raise AssetLocationNotFoundError(str(payload.to_location_id))

        active_history = await self.location_histories.get_active(asset_id)
        location_history = AssetLocationHistory(
            asset_id=asset.id,
            from_location_id=asset.current_location_id,
            to_location_id=payload.to_location_id,
            effective_at=payload.effective_at,
            reason=payload.reason,
            recorded_by=payload.recorded_by,
        )

        async with self.session.begin():
            if active_history is not None:
                await self.location_histories.close_active(
                    active_history,
                    ended_at=payload.effective_at,
                )

            await self.location_histories.create(location_history)
            await self.assets.update(
                asset,
                current_location_id=payload.to_location_id,
                updated_by=payload.recorded_by,
            )

        items = await self.location_histories.list_by_asset(asset_id)
        return items[0]

    async def list_location_history(self, asset_id: UUID) -> list[AssetLocationHistory]:
        await self.get_asset(asset_id)
        items = await self.location_histories.list_by_asset(asset_id)
        return list(items)

    async def create_assignment(
        self,
        asset_id: UUID,
        payload: AssetAssignmentCreate,
    ) -> AssetAssignment:
        asset = await self.get_asset(asset_id)
        if payload.employee_id is None and payload.department_id is None:
            raise AppError(
                code="ASSET_ASSIGNMENT_TARGET_REQUIRED",
                message="Assignment harus memiliki employee_id atau department_id.",
                status_code=422,
            )

        assignment = AssetAssignment(
            asset_id=asset.id,
            assignment_type=payload.assignment_type.value,
            employee_id=payload.employee_id,
            department_id=payload.department_id,
            assigned_at=payload.assigned_at,
            expected_return_date=payload.expected_return_date,
            handover_document_id=payload.handover_document_id,
            accepted_by_employee_at=payload.accepted_by_employee_at,
            released_by_employee_at=payload.released_by_employee_at,
            assignment_status=payload.assignment_status.value,
            notes=payload.notes,
        )

        async with self.session.begin():
            if payload.assignment_type == AssignmentType.PRIMARY_CUSTODIAN:
                active_assignment = await self.assignments.get_active_primary_custodian(asset_id)
                if active_assignment is not None:
                    await self.assignments.close_assignment(
                        active_assignment,
                        returned_at=payload.assigned_at,
                    )

            await self.assignments.create(assignment)

            if payload.assignment_type == AssignmentType.PRIMARY_CUSTODIAN:
                await self.assets.update(
                    asset,
                    current_primary_custodian_id=payload.employee_id,
                )

        items = await self.assignments.list_by_asset(asset_id)
        return items[0]

    async def list_assignment_history(self, asset_id: UUID) -> list[AssetAssignment]:
        await self.get_asset(asset_id)
        items = await self.assignments.list_by_asset(asset_id)
        return list(items)

    async def create_status_change(
        self,
        asset_id: UUID,
        payload: AssetStatusChangeCreate,
    ) -> AssetStatusHistory:
        asset = await self.get_asset(asset_id)
        new_condition = (
            payload.new_condition.value if payload.new_condition else asset.condition_status
        )
        history = AssetStatusHistory(
            asset_id=asset.id,
            previous_status=asset.asset_status,
            new_status=payload.new_status.value,
            previous_condition=asset.condition_status,
            new_condition=new_condition,
            effective_at=payload.effective_at,
            reason=payload.reason,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            changed_by=payload.changed_by,
        )

        async with self.session.begin():
            await self.status_histories.create(history)
            await self.assets.update(
                asset,
                asset_status=payload.new_status.value,
                condition_status=new_condition,
                updated_by=payload.changed_by,
            )

        items = await self.status_histories.list_by_asset(asset_id)
        return items[0]

    async def list_status_history(self, asset_id: UUID) -> list[AssetStatusHistory]:
        await self.get_asset(asset_id)
        items = await self.status_histories.list_by_asset(asset_id)
        return list(items)

    async def get_timeline(self, asset_id: UUID) -> list[AssetTimelineEventRead]:
        await self.get_asset(asset_id)
        location_histories = await self.location_histories.list_by_asset(asset_id)
        assignments = await self.assignments.list_by_asset(asset_id)
        status_histories = await self.status_histories.list_by_asset(asset_id)

        timeline: list[AssetTimelineEventRead] = []

        for item in location_histories:
            timeline.append(
                AssetTimelineEventRead(
                    event_type=AssetTimelineEventType.LOCATION_CHANGE,
                    happened_at=item.effective_at,
                    title="Perubahan lokasi aset",
                    description=item.reason,
                    data={
                        "from_location_id": (
                            str(item.from_location_id) if item.from_location_id else None
                        ),
                        "to_location_id": str(item.to_location_id),
                        "from_location_name": (
                            item.from_location.location_name if item.from_location else None
                        ),
                        "to_location_name": item.to_location.location_name,
                        "recorded_by": str(item.recorded_by) if item.recorded_by else None,
                    },
                )
            )

        for item in assignments:
            timeline.append(
                AssetTimelineEventRead(
                    event_type=AssetTimelineEventType.ASSIGNMENT,
                    happened_at=item.assigned_at,
                    title="Assignment aset",
                    description=item.notes,
                    data={
                        "assignment_type": item.assignment_type,
                        "employee_id": str(item.employee_id) if item.employee_id else None,
                        "department_id": str(item.department_id) if item.department_id else None,
                        "assignment_status": item.assignment_status,
                        "returned_at": item.returned_at.isoformat() if item.returned_at else None,
                    },
                )
            )

        for item in status_histories:
            timeline.append(
                AssetTimelineEventRead(
                    event_type=AssetTimelineEventType.STATUS_CHANGE,
                    happened_at=item.effective_at,
                    title="Perubahan status aset",
                    description=item.reason,
                    data={
                        "previous_status": item.previous_status,
                        "new_status": item.new_status,
                        "previous_condition": item.previous_condition,
                        "new_condition": item.new_condition,
                        "changed_by": str(item.changed_by) if item.changed_by else None,
                    },
                )
            )

        timeline.sort(key=lambda item: item.happened_at, reverse=True)
        return timeline

    async def _validate_asset_relations(
        self,
        asset_category_id: UUID,
        asset_class_id: UUID | None,
        parent_asset_id: UUID | None,
    ) -> None:
        category = await self.asset_categories.get(asset_category_id)
        if category is None:
            raise AssetCategoryNotFoundError(str(asset_category_id))

        if asset_class_id:
            asset_class = await self.asset_classes.get(asset_class_id)
            if asset_class is None:
                raise AssetClassNotFoundError(str(asset_class_id))

        if parent_asset_id:
            parent_asset = await self.assets.get(parent_asset_id)
            if parent_asset is None:
                raise AssetNotFoundError(str(parent_asset_id))

    def _validate_attribute_value(
        self,
        data_type: str,
        payload: AssetAttributeValueCreate,
    ) -> None:
        provided_values = [
            payload.value_text is not None,
            payload.value_number is not None,
            payload.value_date is not None,
            payload.value_boolean is not None,
            payload.value_json is not None,
        ]
        if sum(provided_values) != 1:
            raise AppError(
                code="ASSET_ATTRIBUTE_VALUE_INVALID",
                message="Tepat satu nilai attribute harus diisi.",
                status_code=422,
            )

        allowed_field_by_type = {
            AssetAttributeDataType.TEXT.value: payload.value_text is not None,
            AssetAttributeDataType.NUMBER.value: payload.value_number is not None,
            AssetAttributeDataType.DATE.value: payload.value_date is not None,
            AssetAttributeDataType.BOOLEAN.value: payload.value_boolean is not None,
            AssetAttributeDataType.JSON.value: payload.value_json is not None,
        }
        if not allowed_field_by_type.get(data_type, False):
            raise AppError(
                code="ASSET_ATTRIBUTE_DATA_TYPE_MISMATCH",
                message="Nilai attribute tidak cocok dengan data type definition.",
                status_code=422,
            )

    def _validate_ownership_payload(self, payload: AssetOwnershipCreate) -> None:
        partner_required_types = {
            AssetOwnerType.PARTNER,
            AssetOwnerType.JOINT,
            AssetOwnerType.LESSOR,
            AssetOwnerType.GOVERNMENT,
            AssetOwnerType.OTHER,
        }
        if payload.owner_type in partner_required_types and payload.owner_partner_id is None:
            raise AppError(
                code="ASSET_OWNERSHIP_PARTNER_REQUIRED",
                message="owner_partner_id wajib diisi untuk owner type ini.",
                status_code=422,
            )

        if payload.owner_type == AssetOwnerType.COMPANY and payload.owner_company_id is None:
            raise AppError(
                code="ASSET_OWNERSHIP_COMPANY_REQUIRED",
                message="owner_company_id wajib diisi untuk owner type COMPANY.",
                status_code=422,
            )

        if payload.effective_to and payload.effective_to < payload.effective_from:
            raise AppError(
                code="ASSET_OWNERSHIP_PERIOD_INVALID",
                message="effective_to tidak boleh lebih kecil dari effective_from.",
                status_code=422,
            )

    def _validate_ownership_overlap(
        self,
        existing_items: list[AssetOwnership],
        new_item: AssetOwnership,
    ) -> None:
        total_percentage = 0
        for item in existing_items:
            if self._ownership_periods_overlap(
                item.effective_from,
                item.effective_to,
                new_item.effective_from,
                new_item.effective_to,
            ):
                total_percentage += float(item.ownership_percentage)

        if total_percentage + float(new_item.ownership_percentage) > 100:
            raise AppError(
                code="ASSET_OWNERSHIP_OVER_100",
                message="Total ownership pada periode yang sama tidak boleh melebihi 100%.",
                status_code=409,
            )

    def _ownership_periods_overlap(
        self,
        start_a,
        end_a,
        start_b,
        end_b,
    ) -> bool:
        normalized_end_a = end_a or date.max
        normalized_end_b = end_b or date.max
        return start_a <= normalized_end_b and start_b <= normalized_end_a
