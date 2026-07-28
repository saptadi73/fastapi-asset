from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.assets.constants import AssignmentStatus, AssignmentType
from app.modules.assets.models import (
    Asset,
    AssetAssignment,
    AssetAttributeDefinition,
    AssetAttributeValue,
    AssetCategory,
    AssetClass,
    AssetLifecycleReview,
    AssetLocation,
    AssetLocationHistory,
    AssetOwnership,
    AssetRetirement,
    AssetStatusHistory,
    AssetTransfer,
    AssetTransferItem,
)
from app.shared.pagination import PaginationParams


class AssetCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, category: AssetCategory) -> AssetCategory:
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, category_id: UUID) -> AssetCategory | None:
        return await self.session.get(AssetCategory, category_id)

    async def list(self) -> Sequence[AssetCategory]:
        stmt = select(AssetCategory).order_by(AssetCategory.category_code)
        result = await self.session.scalars(stmt)
        return result.all()


class AssetClassRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, asset_class: AssetClass) -> AssetClass:
        self.session.add(asset_class)
        await self.session.flush()
        return asset_class

    async def get(self, asset_class_id: UUID) -> AssetClass | None:
        return await self.session.get(AssetClass, asset_class_id)

    async def list(self) -> Sequence[AssetClass]:
        result = await self.session.scalars(select(AssetClass).order_by(AssetClass.class_code))
        return result.all()


class AssetLocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, location: AssetLocation) -> AssetLocation:
        self.session.add(location)
        await self.session.flush()
        return location

    async def get(self, location_id: UUID) -> AssetLocation | None:
        return await self.session.get(AssetLocation, location_id)

    async def list(self) -> Sequence[AssetLocation]:
        stmt = select(AssetLocation).order_by(AssetLocation.location_code)
        result = await self.session.scalars(stmt)
        return result.all()


class AssetAttributeDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        definition: AssetAttributeDefinition,
    ) -> AssetAttributeDefinition:
        self.session.add(definition)
        await self.session.flush()
        return definition

    async def get(self, definition_id: UUID) -> AssetAttributeDefinition | None:
        return await self.session.get(AssetAttributeDefinition, definition_id)

    async def list_by_category(
        self,
        asset_category_id: UUID,
    ) -> Sequence[AssetAttributeDefinition]:
        stmt = (
            select(AssetAttributeDefinition)
            .where(AssetAttributeDefinition.asset_category_id == asset_category_id)
            .order_by(AssetAttributeDefinition.attribute_code)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetAttributeValueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        existing: AssetAttributeValue | None,
        new_value: AssetAttributeValue,
    ) -> AssetAttributeValue:
        if existing is not None:
            existing.value_text = new_value.value_text
            existing.value_number = new_value.value_number
            existing.value_date = new_value.value_date
            existing.value_boolean = new_value.value_boolean
            existing.value_json = new_value.value_json
            await self.session.flush()
            return existing

        self.session.add(new_value)
        await self.session.flush()
        return new_value

    async def get_by_asset_and_definition(
        self,
        *,
        asset_id: UUID,
        definition_id: UUID,
    ) -> AssetAttributeValue | None:
        stmt = (
            select(AssetAttributeValue)
            .options(selectinload(AssetAttributeValue.attribute_definition))
            .where(
                and_(
                    AssetAttributeValue.asset_id == asset_id,
                    AssetAttributeValue.attribute_definition_id == definition_id,
                )
            )
        )
        return await self.session.scalar(stmt)

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetAttributeValue]:
        stmt = (
            select(AssetAttributeValue)
            .options(selectinload(AssetAttributeValue.attribute_definition))
            .where(AssetAttributeValue.asset_id == asset_id)
            .order_by(AssetAttributeValue.id)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetOwnershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, ownership: AssetOwnership) -> AssetOwnership:
        self.session.add(ownership)
        await self.session.flush()
        return ownership

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetOwnership]:
        stmt = (
            select(AssetOwnership)
            .where(AssetOwnership.asset_id == asset_id)
            .order_by(AssetOwnership.effective_from.desc(), AssetOwnership.id.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetTransferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, transfer: AssetTransfer) -> AssetTransfer:
        self.session.add(transfer)
        await self.session.flush()
        await self.session.refresh(
            transfer,
            attribute_names=["from_location", "to_location", "items"],
        )
        return transfer

    async def get(self, transfer_id: UUID) -> AssetTransfer | None:
        stmt = (
            select(AssetTransfer)
            .options(
                selectinload(AssetTransfer.from_location),
                selectinload(AssetTransfer.to_location),
                selectinload(AssetTransfer.items),
            )
            .where(AssetTransfer.id == transfer_id)
        )
        return await self.session.scalar(stmt)

    async def list(
        self,
        pagination: PaginationParams,
        *,
        status_filter: str | None = None,
        to_location_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> tuple[Sequence[AssetTransfer], int]:
        stmt: Select[tuple[AssetTransfer]] = select(AssetTransfer).options(
            selectinload(AssetTransfer.from_location),
            selectinload(AssetTransfer.to_location),
            selectinload(AssetTransfer.items),
        )
        count_stmt = select(func.count()).select_from(AssetTransfer)

        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                AssetTransfer.transfer_number.ilike(search_value),
                AssetTransfer.movement_purpose.ilike(search_value),
                AssetTransfer.reason.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if status_filter:
            stmt = stmt.where(AssetTransfer.status == status_filter)
            count_stmt = count_stmt.where(AssetTransfer.status == status_filter)

        if to_location_id:
            stmt = stmt.where(AssetTransfer.to_location_id == to_location_id)
            count_stmt = count_stmt.where(AssetTransfer.to_location_id == to_location_id)

        if requested_by:
            stmt = stmt.where(AssetTransfer.requested_by == requested_by)
            count_stmt = count_stmt.where(AssetTransfer.requested_by == requested_by)

        sort_column = getattr(AssetTransfer, pagination.sort or "transfer_date")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(self, transfer: AssetTransfer, **changes: object) -> AssetTransfer:
        for key, value in changes.items():
            setattr(transfer, key, value)
        await self.session.flush()
        await self.session.refresh(
            transfer,
            attribute_names=["from_location", "to_location", "items"],
        )
        return transfer


class AssetTransferItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(
        self,
        items: list[AssetTransferItem],
    ) -> list[AssetTransferItem]:
        self.session.add_all(items)
        await self.session.flush()
        return items

    async def list_by_transfer(self, transfer_id: UUID) -> Sequence[AssetTransferItem]:
        stmt = (
            select(AssetTransferItem)
            .where(AssetTransferItem.asset_transfer_id == transfer_id)
            .order_by(AssetTransferItem.id)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        await self.session.flush()
        await self.session.refresh(
            asset,
            attribute_names=[
                "asset_category",
                "asset_class",
                "parent_asset",
                "current_location",
                "last_verified_location",
                "attribute_values",
                "ownerships",
                "lifecycle_reviews",
                "retirements",
            ],
        )
        return asset

    async def get(self, asset_id: UUID) -> Asset | None:
        stmt = (
            select(Asset)
            .options(
                selectinload(Asset.asset_category),
                selectinload(Asset.asset_class),
                selectinload(Asset.parent_asset),
                selectinload(Asset.current_location),
                selectinload(Asset.last_verified_location),
                selectinload(Asset.attribute_values).selectinload(
                    AssetAttributeValue.attribute_definition
                ),
                selectinload(Asset.ownerships),
                selectinload(Asset.lifecycle_reviews),
                selectinload(Asset.retirements),
            )
            .where(Asset.id == asset_id)
        )
        return await self.session.scalar(stmt)

    async def get_for_update(self, asset_id: UUID) -> Asset | None:
        stmt = (
            select(Asset)
            .options(
                selectinload(Asset.asset_category),
                selectinload(Asset.asset_class),
                selectinload(Asset.parent_asset),
                selectinload(Asset.current_location),
                selectinload(Asset.last_verified_location),
                selectinload(Asset.attribute_values).selectinload(
                    AssetAttributeValue.attribute_definition
                ),
                selectinload(Asset.ownerships),
                selectinload(Asset.lifecycle_reviews),
                selectinload(Asset.retirements),
            )
            .where(Asset.id == asset_id)
            .with_for_update()
        )
        return await self.session.scalar(stmt)

    async def list(self, pagination: PaginationParams) -> tuple[Sequence[Asset], int]:
        stmt: Select[tuple[Asset]] = select(Asset).options(
            selectinload(Asset.asset_category),
            selectinload(Asset.asset_class),
            selectinload(Asset.parent_asset),
            selectinload(Asset.current_location),
            selectinload(Asset.last_verified_location),
            selectinload(Asset.attribute_values).selectinload(
                AssetAttributeValue.attribute_definition
            ),
            selectinload(Asset.ownerships),
            selectinload(Asset.lifecycle_reviews),
            selectinload(Asset.retirements),
        )
        count_stmt = select(func.count()).select_from(Asset)

        if pagination.search:
            search_value = f"%{pagination.search}%"
            search_filter = or_(
                Asset.asset_code.ilike(search_value),
                Asset.asset_name.ilike(search_value),
                Asset.serial_number.ilike(search_value),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        sort_column = getattr(Asset, pagination.sort or "asset_code")
        if pagination.order == "desc":
            sort_column = sort_column.desc()

        offset = (pagination.page - 1) * pagination.page_size
        stmt = stmt.order_by(sort_column).offset(offset).limit(pagination.page_size)
        items = await self.session.scalars(stmt)
        total_items = await self.session.scalar(count_stmt) or 0
        return items.all(), total_items

    async def update(self, asset: Asset, **changes: object) -> Asset:
        for key, value in changes.items():
            setattr(asset, key, value)
        asset.version_no += 1
        await self.session.flush()
        await self.session.refresh(
            asset,
            attribute_names=[
                "asset_category",
                "asset_class",
                "parent_asset",
                "current_location",
                "last_verified_location",
                "attribute_values",
                "ownerships",
                "lifecycle_reviews",
                "retirements",
            ],
        )
        return asset


class AssetLocationHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, history: AssetLocationHistory) -> AssetLocationHistory:
        self.session.add(history)
        await self.session.flush()
        return history

    async def get_active(self, asset_id: UUID) -> AssetLocationHistory | None:
        stmt = (
            select(AssetLocationHistory)
            .where(
                and_(
                    AssetLocationHistory.asset_id == asset_id,
                    AssetLocationHistory.ended_at.is_(None),
                )
            )
            .order_by(AssetLocationHistory.effective_at.desc())
        )
        return await self.session.scalar(stmt)

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetLocationHistory]:
        stmt = (
            select(AssetLocationHistory)
            .options(
                selectinload(AssetLocationHistory.from_location),
                selectinload(AssetLocationHistory.to_location),
            )
            .where(AssetLocationHistory.asset_id == asset_id)
            .order_by(AssetLocationHistory.effective_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def close_active(
        self,
        history: AssetLocationHistory,
        *,
        ended_at: datetime,
    ) -> AssetLocationHistory:
        history.ended_at = ended_at
        await self.session.flush()
        return history


class AssetAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, assignment: AssetAssignment) -> AssetAssignment:
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def get(self, assignment_id: UUID) -> AssetAssignment | None:
        stmt = select(AssetAssignment).where(AssetAssignment.id == assignment_id)
        return await self.session.scalar(stmt)

    async def get_active_primary_custodian(self, asset_id: UUID) -> AssetAssignment | None:
        stmt = (
            select(AssetAssignment)
            .where(
                and_(
                    AssetAssignment.asset_id == asset_id,
                    AssetAssignment.assignment_type == AssignmentType.PRIMARY_CUSTODIAN.value,
                    AssetAssignment.assignment_status == AssignmentStatus.ACTIVE.value,
                    AssetAssignment.returned_at.is_(None),
                )
            )
            .order_by(AssetAssignment.assigned_at.desc())
        )
        return await self.session.scalar(stmt)

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetAssignment]:
        stmt = (
            select(AssetAssignment)
            .where(AssetAssignment.asset_id == asset_id)
            .order_by(AssetAssignment.assigned_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def close_assignment(
        self,
        assignment: AssetAssignment,
        *,
        returned_at: datetime,
    ) -> AssetAssignment:
        assignment.returned_at = returned_at
        assignment.assignment_status = AssignmentStatus.RETURNED.value
        await self.session.flush()
        return assignment


class AssetStatusHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, history: AssetStatusHistory) -> AssetStatusHistory:
        self.session.add(history)
        await self.session.flush()
        return history

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetStatusHistory]:
        stmt = (
            select(AssetStatusHistory)
            .where(AssetStatusHistory.asset_id == asset_id)
            .order_by(AssetStatusHistory.effective_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetLifecycleReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, review: AssetLifecycleReview) -> AssetLifecycleReview:
        self.session.add(review)
        await self.session.flush()
        return review

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetLifecycleReview]:
        stmt = (
            select(AssetLifecycleReview)
            .where(AssetLifecycleReview.asset_id == asset_id)
            .order_by(
                AssetLifecycleReview.review_date.desc(),
                AssetLifecycleReview.id.desc(),
            )
        )
        result = await self.session.scalars(stmt)
        return result.all()


class AssetRetirementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, retirement: AssetRetirement) -> AssetRetirement:
        self.session.add(retirement)
        await self.session.flush()
        return retirement

    async def get(self, retirement_id: UUID) -> AssetRetirement | None:
        stmt = select(AssetRetirement).where(AssetRetirement.id == retirement_id)
        return await self.session.scalar(stmt)

    async def list_by_asset(self, asset_id: UUID) -> Sequence[AssetRetirement]:
        stmt = (
            select(AssetRetirement)
            .where(AssetRetirement.asset_id == asset_id)
            .order_by(
                AssetRetirement.request_date.desc(),
                AssetRetirement.id.desc(),
            )
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_open_by_asset(self, asset_id: UUID) -> AssetRetirement | None:
        stmt = (
            select(AssetRetirement)
            .where(
                and_(
                    AssetRetirement.asset_id == asset_id,
                    AssetRetirement.status.in_(("REQUESTED", "APPROVED")),
                )
            )
            .order_by(AssetRetirement.request_date.desc(), AssetRetirement.id.desc())
        )
        return await self.session.scalar(stmt)
