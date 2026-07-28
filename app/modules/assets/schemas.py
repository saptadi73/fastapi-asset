from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.constants import (
    AssetAttributeDataType,
    AssetComponentActionType,
    AssetOwnerType,
    AssetRetirementStatus,
    AssetStatus,
    AssetTimelineEventType,
    AssetTransferItemStatus,
    AssetTransferType,
    AssetType,
    AssignmentStatus,
    AssignmentType,
    ConditionStatus,
    ReplacementRecommendation,
)


class AssetCategoryCreate(BaseModel):
    category_code: str = Field(max_length=50)
    category_name: str = Field(max_length=150)
    parent_category_id: UUID | None = None
    description: str | None = None
    is_active: bool = True


class AssetCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_code: str
    category_name: str
    parent_category_id: UUID | None
    description: str | None
    is_active: bool


class AssetClassCreate(BaseModel):
    class_code: str = Field(max_length=50)
    class_name: str = Field(max_length=150)
    description: str | None = None
    sap_asset_class_code: str | None = Field(default=None, max_length=50)
    default_useful_life_months: int | None = Field(default=None, ge=1)
    is_depreciable: bool = True
    is_active: bool = True


class AssetClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_code: str
    class_name: str
    description: str | None
    sap_asset_class_code: str | None
    default_useful_life_months: int | None
    is_depreciable: bool
    is_active: bool


class AssetLocationCreate(BaseModel):
    location_code: str = Field(max_length=50)
    location_name: str = Field(max_length=150)
    location_type: str = Field(max_length=30)
    parent_location_id: UUID | None = None
    company_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_code: str | None = Field(default=None, max_length=50)
    bin_location_code: str | None = Field(default=None, max_length=50)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_active: bool = True


class AssetLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_code: str
    location_name: str
    location_type: str
    parent_location_id: UUID | None
    company_id: UUID | None
    branch_id: UUID | None
    warehouse_code: str | None
    bin_location_code: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool


class AssetAttributeDefinitionCreate(BaseModel):
    asset_category_id: UUID
    attribute_code: str = Field(max_length=50)
    attribute_name: str = Field(max_length=150)
    data_type: AssetAttributeDataType
    unit_of_measure: str | None = Field(default=None, max_length=30)
    is_required: bool = False
    validation_rule: dict | None = None


class AssetAttributeDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_category_id: UUID
    attribute_code: str
    attribute_name: str
    data_type: str
    unit_of_measure: str | None
    is_required: bool
    validation_rule: dict | None


class AssetAttributeValueCreate(BaseModel):
    attribute_definition_id: UUID
    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None
    value_json: dict | None = None


class AssetAttributeValueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    attribute_definition_id: UUID
    value_text: str | None
    value_number: Decimal | None
    value_date: date | None
    value_boolean: bool | None
    value_json: dict | None
    attribute_definition: AssetAttributeDefinitionRead


class AssetOwnershipCreate(BaseModel):
    owner_type: AssetOwnerType
    owner_partner_id: UUID | None = None
    owner_company_id: UUID | None = None
    ownership_percentage: Decimal = Field(gt=0, le=100)
    effective_from: date
    effective_to: date | None = None
    source_reference: str | None = Field(default=None, max_length=150)
    notes: str | None = None


class AssetOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    owner_type: str
    owner_partner_id: UUID | None
    owner_company_id: UUID | None
    ownership_percentage: Decimal
    effective_from: date
    effective_to: date | None
    source_reference: str | None
    notes: str | None


class AssetTransferItemCreate(BaseModel):
    asset_id: UUID
    previous_custodian_id: UUID | None = None
    new_custodian_id: UUID | None = None
    handover_condition: str = Field(max_length=30)
    dispatch_scan_event_id: UUID | None = None
    receipt_scan_event_id: UUID | None = None
    item_status: AssetTransferItemStatus = AssetTransferItemStatus.PENDING
    notes: str | None = None


class AssetTransferCreate(BaseModel):
    transfer_number: str = Field(max_length=50)
    transfer_date: datetime
    transfer_type: AssetTransferType
    movement_purpose: str = Field(max_length=30)
    is_permanent: bool = True
    expected_return_at: datetime | None = None
    from_location_id: UUID | None = None
    to_location_id: UUID
    from_department_id: UUID | None = None
    to_department_id: UUID | None = None
    requested_by: UUID | None = None
    reason: str | None = None
    items: list[AssetTransferItemCreate]


class AssetTransferActionPayload(BaseModel):
    actor_id: UUID | None = None
    acted_at: datetime


class AssetTransferItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_transfer_id: UUID
    asset_id: UUID
    previous_custodian_id: UUID | None
    new_custodian_id: UUID | None
    handover_condition: str
    dispatch_scan_event_id: UUID | None
    receipt_scan_event_id: UUID | None
    item_status: str
    notes: str | None


class AssetTransferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transfer_number: str
    transfer_date: datetime
    transfer_type: str
    status: str
    movement_purpose: str
    is_permanent: bool
    expected_return_at: datetime | None
    from_location_id: UUID | None
    to_location_id: UUID
    from_department_id: UUID | None
    to_department_id: UUID | None
    requested_by: UUID | None
    approved_by: UUID | None
    approved_at: datetime | None
    dispatched_by: UUID | None
    dispatched_at: datetime | None
    received_by: UUID | None
    received_at: datetime | None
    reason: str | None
    from_location: AssetLocationRead | None = None
    to_location: AssetLocationRead
    items: list[AssetTransferItemRead]


class AssetTransferListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transfer_number: str
    transfer_date: datetime
    transfer_type: str
    status: str
    movement_purpose: str
    is_permanent: bool
    from_location_id: UUID | None
    to_location_id: UUID
    requested_by: UUID | None
    approved_by: UUID | None
    approved_at: datetime | None
    received_at: datetime | None
    reason: str | None
    from_location: AssetLocationRead | None = None
    to_location: AssetLocationRead
    item_count: int


class AssetCreate(BaseModel):
    asset_code: str = Field(max_length=50)
    asset_name: str = Field(max_length=200)
    description: str | None = None
    asset_category_id: UUID
    asset_class_id: UUID | None = None
    parent_asset_id: UUID | None = None
    asset_type: AssetType
    asset_status: AssetStatus
    condition_status: ConditionStatus
    criticality_level: str | None = Field(default=None, max_length=20)
    serial_number: str | None = Field(default=None, max_length=150)
    manufacturer_id: UUID | None = None
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    manufacture_year: int | None = Field(default=None, ge=1900, le=2200)
    company_id: UUID | None = None
    branch_id: UUID | None = None
    current_location_id: UUID | None = None
    current_primary_custodian_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=100)
    qr_code: str | None = Field(default=None, max_length=200)
    tag_number: str | None = Field(default=None, max_length=100)
    tracking_status: str = Field(default="TRACKED", max_length=20)
    last_verified_at: datetime | None = None
    last_verified_location_id: UUID | None = None
    in_service_date: date | None = None
    retirement_date: date | None = None
    expected_replacement_date: date | None = None
    support_end_date: date | None = None
    vendor_end_of_sale_date: date | None = None
    vendor_end_of_support_date: date | None = None
    replacement_strategy: str | None = Field(default=None, max_length=30)
    replacement_priority: str | None = Field(default=None, max_length=20)
    estimated_replacement_cost: Decimal | None = None
    replacement_budget_year: int | None = Field(default=None, ge=1900, le=2200)
    next_review_date: date | None = None
    sap_asset_code: str | None = Field(default=None, max_length=50)
    sap_item_code: str | None = Field(default=None, max_length=50)
    created_by: UUID | None = None
    updated_by: UUID | None = None


class AssetUpdate(BaseModel):
    asset_name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    asset_class_id: UUID | None = None
    parent_asset_id: UUID | None = None
    asset_status: AssetStatus | None = None
    condition_status: ConditionStatus | None = None
    criticality_level: str | None = Field(default=None, max_length=20)
    serial_number: str | None = Field(default=None, max_length=150)
    manufacturer_id: UUID | None = None
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    manufacture_year: int | None = Field(default=None, ge=1900, le=2200)
    current_location_id: UUID | None = None
    current_primary_custodian_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=100)
    qr_code: str | None = Field(default=None, max_length=200)
    tag_number: str | None = Field(default=None, max_length=100)
    tracking_status: str | None = Field(default=None, max_length=20)
    last_verified_at: datetime | None = None
    last_verified_location_id: UUID | None = None
    in_service_date: date | None = None
    retirement_date: date | None = None
    expected_replacement_date: date | None = None
    support_end_date: date | None = None
    vendor_end_of_sale_date: date | None = None
    vendor_end_of_support_date: date | None = None
    replacement_strategy: str | None = Field(default=None, max_length=30)
    replacement_priority: str | None = Field(default=None, max_length=20)
    estimated_replacement_cost: Decimal | None = None
    replacement_budget_year: int | None = Field(default=None, ge=1900, le=2200)
    next_review_date: date | None = None
    sap_asset_code: str | None = Field(default=None, max_length=50)
    sap_item_code: str | None = Field(default=None, max_length=50)
    updated_by: UUID | None = None


class AssetReference(BaseModel):
    id: UUID
    code: str
    name: str


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_code: str
    asset_name: str
    description: str | None
    asset_type: str
    asset_status: str
    condition_status: str
    criticality_level: str | None
    serial_number: str | None
    brand: str | None
    model: str | None
    manufacture_year: int | None
    company_id: UUID | None
    branch_id: UUID | None
    current_location_id: UUID | None
    current_primary_custodian_id: UUID | None
    barcode: str | None
    qr_code: str | None
    tag_number: str | None
    tracking_status: str
    last_verified_at: datetime | None
    last_verified_location_id: UUID | None
    in_service_date: date | None
    retirement_date: date | None
    expected_replacement_date: date | None
    support_end_date: date | None
    vendor_end_of_sale_date: date | None
    vendor_end_of_support_date: date | None
    replacement_strategy: str | None
    replacement_priority: str | None
    estimated_replacement_cost: Decimal | None
    replacement_budget_year: int | None
    next_review_date: date | None
    sap_asset_code: str | None
    sap_item_code: str | None
    version_no: int
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None
    asset_category: AssetCategoryRead
    asset_class: AssetClassRead | None
    current_location: AssetLocationRead | None = None
    attributes: list[AssetAttributeValueRead] = []
    parent_asset: AssetReference | None = None

    @classmethod
    def from_model(cls, asset: object) -> AssetRead:
        parent_asset = None
        if getattr(asset, "parent_asset", None):
            parent_asset = AssetReference(
                id=asset.parent_asset.id,
                code=asset.parent_asset.asset_code,
                name=asset.parent_asset.asset_name,
            )

        return cls(
            id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            description=asset.description,
            asset_type=asset.asset_type,
            asset_status=asset.asset_status,
            condition_status=asset.condition_status,
            criticality_level=asset.criticality_level,
            serial_number=asset.serial_number,
            brand=asset.brand,
            model=asset.model,
            manufacture_year=asset.manufacture_year,
            company_id=asset.company_id,
            branch_id=asset.branch_id,
            current_location_id=asset.current_location_id,
            current_primary_custodian_id=asset.current_primary_custodian_id,
            barcode=asset.barcode,
            qr_code=asset.qr_code,
            tag_number=asset.tag_number,
            tracking_status=asset.tracking_status,
            last_verified_at=asset.last_verified_at,
            last_verified_location_id=asset.last_verified_location_id,
            in_service_date=asset.in_service_date,
            retirement_date=asset.retirement_date,
            expected_replacement_date=asset.expected_replacement_date,
            support_end_date=asset.support_end_date,
            vendor_end_of_sale_date=asset.vendor_end_of_sale_date,
            vendor_end_of_support_date=asset.vendor_end_of_support_date,
            replacement_strategy=asset.replacement_strategy,
            replacement_priority=asset.replacement_priority,
            estimated_replacement_cost=asset.estimated_replacement_cost,
            replacement_budget_year=asset.replacement_budget_year,
            next_review_date=asset.next_review_date,
            sap_asset_code=asset.sap_asset_code,
            sap_item_code=asset.sap_item_code,
            version_no=asset.version_no,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            created_by=asset.created_by,
            updated_by=asset.updated_by,
            asset_category=AssetCategoryRead.model_validate(asset.asset_category),
            asset_class=(
                AssetClassRead.model_validate(asset.asset_class) if asset.asset_class else None
            ),
            current_location=(
                AssetLocationRead.model_validate(asset.current_location)
                if asset.current_location
                else None
            ),
            attributes=[
                AssetAttributeValueRead.model_validate(item)
                for item in getattr(asset, "attribute_values", [])
            ],
            parent_asset=parent_asset,
        )


class AssetLocationChangeCreate(BaseModel):
    to_location_id: UUID
    effective_at: datetime
    reason: str | None = None
    recorded_by: UUID | None = None


class AssetLocationHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    from_location_id: UUID | None
    to_location_id: UUID
    effective_at: datetime
    ended_at: datetime | None
    transfer_id: UUID | None
    reason: str | None
    recorded_by: UUID | None
    from_location: AssetLocationRead | None = None
    to_location: AssetLocationRead


class AssetAssignmentCreate(BaseModel):
    assignment_type: AssignmentType
    employee_id: UUID | None = None
    department_id: UUID | None = None
    assigned_at: datetime
    expected_return_date: date | None = None
    handover_document_id: UUID | None = None
    accepted_by_employee_at: datetime | None = None
    released_by_employee_at: datetime | None = None
    assignment_status: AssignmentStatus = AssignmentStatus.ACTIVE
    notes: str | None = None


class AssetAssignmentReturnPayload(BaseModel):
    returned_at: datetime
    released_by_employee_at: datetime | None = None
    notes: str | None = None


class AssetAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    assignment_type: str
    employee_id: UUID | None
    department_id: UUID | None
    assigned_at: datetime
    expected_return_date: date | None
    returned_at: datetime | None
    handover_document_id: UUID | None
    accepted_by_employee_at: datetime | None
    released_by_employee_at: datetime | None
    assignment_status: str
    notes: str | None


class AssetStatusChangeCreate(BaseModel):
    new_status: AssetStatus
    new_condition: ConditionStatus | None = None
    effective_at: datetime
    reason: str | None = None
    reference_type: str | None = Field(default=None, max_length=50)
    reference_id: UUID | None = None
    changed_by: UUID | None = None


class AssetStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    previous_status: str | None
    new_status: str
    previous_condition: str | None
    new_condition: str | None
    effective_at: datetime
    reason: str | None
    reference_type: str | None
    reference_id: UUID | None
    changed_by: UUID | None


class AssetTimelineEventRead(BaseModel):
    event_type: AssetTimelineEventType
    happened_at: datetime
    title: str
    description: str | None
    data: dict


class AssetComponentChangeCreate(BaseModel):
    action_type: AssetComponentActionType
    effective_at: datetime
    installed_component_asset_id: UUID | None = None
    removed_component_asset_id: UUID | None = None
    reason: str | None = None
    work_order_id: UUID | None = None
    reference_type: str | None = Field(default=None, max_length=50)
    reference_id: UUID | None = None


class AssetComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_code: str
    asset_name: str
    asset_status: str
    condition_status: str
    serial_number: str | None
    parent_asset_id: UUID | None

    @classmethod
    def from_model(cls, asset: object) -> AssetComponentRead:
        return cls(
            id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            asset_status=asset.asset_status,
            condition_status=asset.condition_status,
            serial_number=asset.serial_number,
            parent_asset_id=asset.parent_asset_id,
        )


class AssetComponentHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    action_type: AssetComponentActionType
    removed_component_asset_id: UUID | None
    installed_component_asset_id: UUID | None
    effective_at: datetime
    reason: str | None
    work_order_id: UUID | None
    reference_type: str | None
    reference_id: UUID | None
    changed_by: UUID | None
    removed_component_asset: AssetComponentRead | None = None
    installed_component_asset: AssetComponentRead | None = None


class AssetLifecycleReviewCreate(BaseModel):
    review_date: date
    condition_score: Decimal = Field(ge=0, le=100)
    remaining_life_months: int | None = Field(default=None, ge=0)
    risk_score: Decimal | None = Field(default=None, ge=0, le=100)
    replacement_recommendation: ReplacementRecommendation
    estimated_replacement_cost: Decimal | None = None
    review_notes: str | None = None
    approved_by: UUID | None = None


class AssetLifecycleReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    review_date: date
    condition_score: Decimal
    remaining_life_months: int | None
    risk_score: Decimal | None
    replacement_recommendation: str
    estimated_replacement_cost: Decimal | None
    review_notes: str | None
    reviewed_by: UUID | None
    approved_by: UUID | None


class AssetRetirementRequestCreate(BaseModel):
    retirement_number: str = Field(max_length=50)
    retirement_type: str = Field(max_length=30)
    request_date: date
    proceeds_amount: Decimal = Field(default=Decimal("0"), ge=0)
    buyer_partner_id: UUID | None = None
    reason: str | None = None


class AssetRetirementApprovePayload(BaseModel):
    approved_by: UUID | None = None


class AssetRetirementConfirmPayload(BaseModel):
    effective_date: date
    sap_retirement_doc_entry: int | None = Field(default=None, ge=1)
    sap_trans_id: int | None = Field(default=None, ge=1)
    final_asset_status: AssetStatus | None = None


class AssetRetirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    retirement_number: str
    retirement_type: str
    request_date: date
    effective_date: date | None
    status: AssetRetirementStatus
    proceeds_amount: Decimal
    buyer_partner_id: UUID | None
    reason: str | None
    approved_by: UUID | None
    sap_retirement_doc_entry: int | None
    sap_trans_id: int | None
