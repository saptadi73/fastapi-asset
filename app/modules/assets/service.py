from datetime import date, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.compat import UTC
from app.core.exceptions import AppError
from app.modules.assets.constants import (
    AssetAttributeDataType,
    AssetComponentActionType,
    AssetOwnerType,
    AssetRetirementStatus,
    AssetStatus,
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
    AssetComponentHistory,
    AssetLifecycleReview,
    AssetLocation,
    AssetLocationHistory,
    AssetOwnership,
    AssetRetirement,
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
    AssetComponentHistoryRepository,
    AssetLifecycleReviewRepository,
    AssetLocationHistoryRepository,
    AssetLocationRepository,
    AssetOwnershipRepository,
    AssetRepository,
    AssetRetirementRepository,
    AssetStatusHistoryRepository,
    AssetTransferItemRepository,
    AssetTransferRepository,
)
from app.modules.assets.schemas import (
    AssetAssignmentCreate,
    AssetAssignmentReturnPayload,
    AssetAttributeDefinitionCreate,
    AssetAttributeValueCreate,
    AssetCategoryCreate,
    AssetClassCreate,
    AssetComponentChangeCreate,
    AssetCreate,
    AssetLifecycleReviewCreate,
    AssetLocationChangeCreate,
    AssetLocationCreate,
    AssetOwnershipCreate,
    AssetRetirementConfirmPayload,
    AssetRetirementRequestCreate,
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
        self.lifecycle_reviews = AssetLifecycleReviewRepository(session)
        self.retirements = AssetRetirementRepository(session)
        self.component_histories = AssetComponentHistoryRepository(session)

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

        definition_data = payload.model_dump(mode="python")
        definition_data["data_type"] = payload.data_type.value
        definition = AssetAttributeDefinition(**definition_data)
        try:
            await self.attribute_definitions.create(definition)
            await self.session.commit()
            return definition
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ASSET_ATTRIBUTE_DEFINITION_CONFLICT",
                message="Attribute code sudah digunakan pada kategori ini.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

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

        asset_data = payload.model_dump(mode="python")
        asset_data["asset_type"] = payload.asset_type.value
        asset_data["asset_status"] = payload.asset_status.value
        asset_data["condition_status"] = payload.condition_status.value
        asset = Asset(**asset_data)
        try:
            await self.assets.create(asset)
            await self.session.commit()
            return await self.get_asset(asset.id)
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ASSET_CONFLICT",
                message="Asset code sudah digunakan atau relasi tidak valid.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

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
            await self.assets.update(asset, **changes)
            await self.session.commit()
            return await self.get_asset(asset.id)
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ASSET_UPDATE_CONFLICT",
                message="Perubahan asset menimbulkan konflik data.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

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

        try:
            await self.attribute_values.upsert(existing=existing, new_value=new_value)
            await self.assets.update(asset, updated_by=asset.updated_by)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

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

        try:
            await self.ownerships.create(ownership)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

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
            created_transfer = await self.transfers.create(transfer)
            for item in items:
                item.asset_transfer_id = created_transfer.id
            await self.transfer_items.create_many(items)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ASSET_TRANSFER_CONFLICT",
                message="Transfer number sudah digunakan atau item asset duplikat.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        return await self.get_transfer(created_transfer.id)

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

        try:
            await self.transfers.update(
                transfer,
                status=AssetTransferStatus.SUBMITTED.value,
                requested_by=payload.actor_id or transfer.requested_by,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
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

        try:
            await self.transfers.update(
                transfer,
                status=AssetTransferStatus.APPROVED.value,
                approved_by=payload.actor_id,
                approved_at=payload.acted_at,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
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

        try:
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
                    current_primary_custodian_id=(
                        item.new_custodian_id
                        if item.new_custodian_id is not None
                        else asset.current_primary_custodian_id
                    ),
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
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

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

        try:
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
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

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

        try:
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
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        items = await self.assignments.list_by_asset(asset_id)
        return items[0]

    async def list_assignment_history(self, asset_id: UUID) -> list[AssetAssignment]:
        await self.get_asset(asset_id)
        items = await self.assignments.list_by_asset(asset_id)
        return list(items)

    async def change_components(
        self,
        asset_id: UUID,
        payload: AssetComponentChangeCreate,
        *,
        changed_by: UUID | None,
    ) -> AssetComponentHistory:
        asset = await self.assets.get_for_update(asset_id)
        if asset is None:
            raise AssetNotFoundError(str(asset_id))

        removed_component: Asset | None = None
        installed_component: Asset | None = None

        if payload.removed_component_asset_id is not None:
            removed_component = await self.assets.get_for_update(
                payload.removed_component_asset_id
            )
            if removed_component is None:
                raise AssetNotFoundError(str(payload.removed_component_asset_id))

        if payload.installed_component_asset_id is not None:
            installed_component = await self.assets.get_for_update(
                payload.installed_component_asset_id
            )
            if installed_component is None:
                raise AssetNotFoundError(str(payload.installed_component_asset_id))

        self._validate_component_change(
            host_asset=asset,
            payload=payload,
            removed_component=removed_component,
            installed_component=installed_component,
        )

        history = AssetComponentHistory(
            asset_id=asset.id,
            action_type=payload.action_type.value,
            removed_component_asset_id=payload.removed_component_asset_id,
            installed_component_asset_id=payload.installed_component_asset_id,
            effective_at=payload.effective_at,
            reason=payload.reason,
            work_order_id=payload.work_order_id,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            changed_by=changed_by,
        )

        try:
            if removed_component is not None:
                await self.assets.update(
                    removed_component,
                    parent_asset_id=None,
                    updated_by=changed_by,
                )

            if installed_component is not None:
                await self.assets.update(
                    installed_component,
                    parent_asset_id=asset.id,
                    current_location_id=asset.current_location_id,
                    updated_by=changed_by,
                )

            await self.component_histories.create(history)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        items = await self.component_histories.list_by_asset(asset_id)
        return items[0]

    async def list_components(self, asset_id: UUID) -> list[Asset]:
        await self.get_asset(asset_id)
        items = await self.assets.list_children(asset_id)
        return list(items)

    async def list_component_history(self, asset_id: UUID) -> list[AssetComponentHistory]:
        await self.get_asset(asset_id)
        items = await self.component_histories.list_by_asset(asset_id)
        return list(items)

    async def return_assignment(
        self,
        assignment_id: UUID,
        payload: AssetAssignmentReturnPayload,
    ) -> AssetAssignment:
        assignment = await self.assignments.get(assignment_id)
        if assignment is None:
            raise AppError(
                code="ASSET_ASSIGNMENT_NOT_FOUND",
                message="Assignment asset tidak ditemukan.",
                status_code=404,
            )
        if assignment.returned_at is not None:
            raise AppError(
                code="ASSET_ASSIGNMENT_ALREADY_RETURNED",
                message="Assignment asset sudah dikembalikan sebelumnya.",
                status_code=409,
            )
        if payload.returned_at < assignment.assigned_at:
            raise AppError(
                code="ASSET_ASSIGNMENT_RETURN_TIME_INVALID",
                message="returned_at tidak boleh lebih kecil dari assigned_at.",
                status_code=422,
            )

        asset = await self.get_asset(assignment.asset_id)
        try:
            await self.assignments.close_assignment(
                assignment,
                returned_at=payload.returned_at,
            )
            assignment.released_by_employee_at = (
                payload.released_by_employee_at or payload.returned_at
            )
            if payload.notes:
                assignment.notes = payload.notes
            await self.session.flush()

            if (
                assignment.assignment_type == AssignmentType.PRIMARY_CUSTODIAN.value
                and asset.current_primary_custodian_id == assignment.employee_id
            ):
                await self.assets.update(asset, current_primary_custodian_id=None)

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        items = await self.assignments.list_by_asset(assignment.asset_id)
        return items[0]

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

        try:
            await self.status_histories.create(history)
            await self.assets.update(
                asset,
                asset_status=payload.new_status.value,
                condition_status=new_condition,
                updated_by=payload.changed_by,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        items = await self.status_histories.list_by_asset(asset_id)
        return items[0]

    async def list_status_history(self, asset_id: UUID) -> list[AssetStatusHistory]:
        await self.get_asset(asset_id)
        items = await self.status_histories.list_by_asset(asset_id)
        return list(items)

    async def create_lifecycle_review(
        self,
        asset_id: UUID,
        payload: AssetLifecycleReviewCreate,
        *,
        reviewed_by: UUID | None,
    ) -> AssetLifecycleReview:
        asset = await self.get_asset(asset_id)
        review = AssetLifecycleReview(
            asset_id=asset.id,
            review_date=payload.review_date,
            condition_score=payload.condition_score,
            remaining_life_months=payload.remaining_life_months,
            risk_score=payload.risk_score,
            replacement_recommendation=payload.replacement_recommendation.value,
            estimated_replacement_cost=payload.estimated_replacement_cost,
            review_notes=payload.review_notes,
            reviewed_by=reviewed_by,
            approved_by=payload.approved_by,
        )

        try:
            await self.lifecycle_reviews.create(review)
            await self.assets.update(
                asset,
                next_review_date=payload.review_date,
                estimated_replacement_cost=(
                    payload.estimated_replacement_cost or asset.estimated_replacement_cost
                ),
                updated_by=reviewed_by,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ASSET_LIFECYCLE_REVIEW_CONFLICT",
                message="Lifecycle review untuk tanggal tersebut sudah ada.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        items = await self.lifecycle_reviews.list_by_asset(asset_id)
        return items[0]

    async def list_lifecycle_reviews(self, asset_id: UUID) -> list[AssetLifecycleReview]:
        await self.get_asset(asset_id)
        items = await self.lifecycle_reviews.list_by_asset(asset_id)
        return list(items)

    async def create_retirement_request(
        self,
        asset_id: UUID,
        payload: AssetRetirementRequestCreate,
    ) -> AssetRetirement:
        asset = await self.get_asset(asset_id)
        open_request = await self.retirements.get_open_by_asset(asset_id)
        if open_request is not None:
            raise AppError(
                code="ASSET_RETIREMENT_ALREADY_OPEN",
                message="Masih ada retirement request yang belum selesai untuk asset ini.",
                status_code=409,
            )
        if asset.asset_status in {AssetStatus.RETIRED.value, AssetStatus.DISPOSED.value}:
            raise AppError(
                code="ASSET_ALREADY_RETIRED",
                message="Asset sudah berada pada status retired/disposed.",
                status_code=409,
            )

        retirement = AssetRetirement(
            asset_id=asset.id,
            retirement_number=payload.retirement_number,
            retirement_type=payload.retirement_type,
            request_date=payload.request_date,
            status=AssetRetirementStatus.REQUESTED.value,
            proceeds_amount=payload.proceeds_amount,
            buyer_partner_id=payload.buyer_partner_id,
            reason=payload.reason,
        )

        try:
            await self.retirements.create(retirement)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                code="ASSET_RETIREMENT_CONFLICT",
                message="Retirement number sudah digunakan.",
                status_code=409,
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

        items = await self.retirements.list_by_asset(asset_id)
        return items[0]

    async def list_retirement_requests(self, asset_id: UUID) -> list[AssetRetirement]:
        await self.get_asset(asset_id)
        items = await self.retirements.list_by_asset(asset_id)
        return list(items)

    async def get_retirement_request(self, retirement_id: UUID) -> AssetRetirement:
        item = await self.retirements.get(retirement_id)
        if item is None:
            raise AppError(
                code="ASSET_RETIREMENT_NOT_FOUND",
                message="Retirement request tidak ditemukan.",
                status_code=404,
            )
        return item

    async def approve_retirement_request(
        self,
        retirement_id: UUID,
        *,
        approved_by: UUID | None,
    ) -> AssetRetirement:
        item = await self.get_retirement_request(retirement_id)
        if item.status != AssetRetirementStatus.REQUESTED.value:
            raise AppError(
                code="ASSET_RETIREMENT_INVALID_STATUS",
                message="Hanya retirement request berstatus REQUESTED yang dapat diapprove.",
                status_code=409,
            )

        item.status = AssetRetirementStatus.APPROVED.value
        item.approved_by = approved_by
        await self.session.commit()
        return await self.get_retirement_request(retirement_id)

    async def confirm_retirement_request(
        self,
        retirement_id: UUID,
        payload: AssetRetirementConfirmPayload,
        *,
        changed_by: UUID | None,
    ) -> AssetRetirement:
        retirement = await self.get_retirement_request(retirement_id)
        if retirement.status not in {
            AssetRetirementStatus.REQUESTED.value,
            AssetRetirementStatus.APPROVED.value,
        }:
            raise AppError(
                code="ASSET_RETIREMENT_INVALID_STATUS",
                message="Retirement request tidak dapat dikonfirmasi pada status saat ini.",
                status_code=409,
            )

        asset = await self.assets.get_for_update(retirement.asset_id)
        if asset is None:
            raise AssetNotFoundError(str(retirement.asset_id))

        final_status = (
            payload.final_asset_status.value
            if payload.final_asset_status is not None
            else self._default_retirement_asset_status(retirement.retirement_type)
        )
        if final_status not in {AssetStatus.RETIRED.value, AssetStatus.DISPOSED.value}:
            raise AppError(
                code="ASSET_RETIREMENT_FINAL_STATUS_INVALID",
                message="final_asset_status harus RETIRED atau DISPOSED.",
                status_code=422,
            )

        status_history = AssetStatusHistory(
            asset_id=asset.id,
            previous_status=asset.asset_status,
            new_status=final_status,
            previous_condition=asset.condition_status,
            new_condition=asset.condition_status,
            effective_at=datetime.combine(payload.effective_date, datetime.min.time(), UTC),
            reason=retirement.reason,
            reference_type="ASSET_RETIREMENT",
            reference_id=retirement.id,
            changed_by=changed_by,
        )

        try:
            retirement.status = AssetRetirementStatus.CONFIRMED.value
            retirement.effective_date = payload.effective_date
            retirement.sap_retirement_doc_entry = payload.sap_retirement_doc_entry
            retirement.sap_trans_id = payload.sap_trans_id
            await self.status_histories.create(status_history)
            await self.assets.update(
                asset,
                asset_status=final_status,
                retirement_date=payload.effective_date,
                updated_by=changed_by,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return await self.get_retirement_request(retirement_id)

    async def get_timeline(self, asset_id: UUID) -> list[AssetTimelineEventRead]:
        await self.get_asset(asset_id)
        location_histories = await self.location_histories.list_by_asset(asset_id)
        assignments = await self.assignments.list_by_asset(asset_id)
        status_histories = await self.status_histories.list_by_asset(asset_id)
        lifecycle_reviews = await self.lifecycle_reviews.list_by_asset(asset_id)
        retirements = await self.retirements.list_by_asset(asset_id)
        component_histories = await self.component_histories.list_by_asset(asset_id)

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

        for item in lifecycle_reviews:
            timeline.append(
                AssetTimelineEventRead(
                    event_type=AssetTimelineEventType.LIFECYCLE_REVIEW,
                    happened_at=datetime.combine(item.review_date, datetime.min.time(), UTC),
                    title="Lifecycle review asset",
                    description=item.review_notes,
                    data={
                        "condition_score": str(item.condition_score),
                        "remaining_life_months": item.remaining_life_months,
                        "risk_score": str(item.risk_score) if item.risk_score is not None else None,
                        "replacement_recommendation": item.replacement_recommendation,
                        "estimated_replacement_cost": (
                            str(item.estimated_replacement_cost)
                            if item.estimated_replacement_cost is not None
                            else None
                        ),
                        "reviewed_by": str(item.reviewed_by) if item.reviewed_by else None,
                    },
                )
            )

        for item in retirements:
            happened_at = item.effective_date or item.request_date
            timeline.append(
                AssetTimelineEventRead(
                    event_type=AssetTimelineEventType.RETIREMENT,
                    happened_at=datetime.combine(happened_at, datetime.min.time(), UTC),
                    title="Retirement request asset",
                    description=item.reason,
                    data={
                        "retirement_number": item.retirement_number,
                        "retirement_type": item.retirement_type,
                        "status": item.status,
                        "effective_date": (
                            item.effective_date.isoformat() if item.effective_date else None
                        ),
                        "sap_retirement_doc_entry": item.sap_retirement_doc_entry,
                        "sap_trans_id": item.sap_trans_id,
                    },
                )
            )

        for item in component_histories:
            timeline.append(
                AssetTimelineEventRead(
                    event_type=AssetTimelineEventType.COMPONENT_CHANGE,
                    happened_at=item.effective_at,
                    title="Perubahan komponen asset",
                    description=item.reason,
                    data={
                        "action_type": item.action_type,
                        "removed_component_asset_id": (
                            str(item.removed_component_asset_id)
                            if item.removed_component_asset_id
                            else None
                        ),
                        "installed_component_asset_id": (
                            str(item.installed_component_asset_id)
                            if item.installed_component_asset_id
                            else None
                        ),
                        "removed_component_asset_code": (
                            item.removed_component_asset.asset_code
                            if item.removed_component_asset
                            else None
                        ),
                        "installed_component_asset_code": (
                            item.installed_component_asset.asset_code
                            if item.installed_component_asset
                            else None
                        ),
                        "work_order_id": str(item.work_order_id) if item.work_order_id else None,
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

    def _default_retirement_asset_status(self, retirement_type: str) -> str:
        normalized = retirement_type.upper()
        if normalized in {"SALE", "SCRAP", "DISPOSAL"}:
            return AssetStatus.DISPOSED.value
        return AssetStatus.RETIRED.value

    def _validate_component_change(
        self,
        *,
        host_asset: Asset,
        payload: AssetComponentChangeCreate,
        removed_component: Asset | None,
        installed_component: Asset | None,
    ) -> None:
        if payload.action_type == AssetComponentActionType.INSTALL:
            if installed_component is None or removed_component is not None:
                raise AppError(
                    code="ASSET_COMPONENT_ACTION_INVALID",
                    message="Action INSTALL wajib hanya membawa installed_component_asset_id.",
                    status_code=422,
                )

        if payload.action_type == AssetComponentActionType.REMOVE:
            if removed_component is None or installed_component is not None:
                raise AppError(
                    code="ASSET_COMPONENT_ACTION_INVALID",
                    message="Action REMOVE wajib hanya membawa removed_component_asset_id.",
                    status_code=422,
                )

        if payload.action_type == AssetComponentActionType.REPLACE:
            if removed_component is None or installed_component is None:
                raise AppError(
                    code="ASSET_COMPONENT_ACTION_INVALID",
                    message="Action REPLACE wajib membawa removed dan installed component.",
                    status_code=422,
                )

        involved_assets = [item for item in (removed_component, installed_component) if item]
        for component in involved_assets:
            if component.id == host_asset.id:
                raise AppError(
                    code="ASSET_COMPONENT_SELF_REFERENCE",
                    message="Asset host tidak boleh menjadi komponennya sendiri.",
                    status_code=409,
                )

        if removed_component is not None and removed_component.parent_asset_id != host_asset.id:
            raise AppError(
                code="ASSET_COMPONENT_NOT_INSTALLED",
                message="Komponen yang akan dilepas tidak terpasang pada asset host ini.",
                status_code=409,
            )

        if installed_component is not None:
            if installed_component.parent_asset_id is not None:
                raise AppError(
                    code="ASSET_COMPONENT_ALREADY_ATTACHED",
                    message="Komponen yang akan dipasang masih terhubung ke asset lain.",
                    status_code=409,
                )
            if self._creates_component_cycle(host_asset=host_asset, component=installed_component):
                raise AppError(
                    code="ASSET_COMPONENT_CYCLE",
                    message="Pemasangan komponen menimbulkan siklus hierarchy asset.",
                    status_code=409,
                )

        if (
            removed_component is not None
            and installed_component is not None
            and removed_component.id == installed_component.id
        ):
            raise AppError(
                code="ASSET_COMPONENT_REPLACE_SAME_ASSET",
                message="Komponen pengganti harus berbeda dari komponen yang dilepas.",
                status_code=409,
            )

    def _creates_component_cycle(self, *, host_asset: Asset, component: Asset) -> bool:
        current = host_asset
        while current is not None:
            if current.id == component.id:
                return True
            current = getattr(current, "parent_asset", None)
        return False

