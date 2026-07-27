from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_session,
    require_maintenance_read,
    require_maintenance_report_read,
    require_maintenance_write,
)
from app.modules.attachments.constants import AttachmentEntityType
from app.modules.attachments.schemas import AttachmentCreate, AttachmentRead
from app.modules.attachments.service import AttachmentService
from app.modules.auth.models import AppUser
from app.modules.maintenance.schemas import (
    AssetFailureCreate,
    AssetFailureListItemRead,
    AssetFailureRead,
    AssetFailureUpdate,
    MaintenanceChecklistExecutionRead,
    MaintenanceChecklistExecutionStartPayload,
    MaintenanceChecklistResultSubmitPayload,
    MaintenanceChecklistTemplateCreate,
    MaintenanceChecklistTemplateRead,
    MaintenanceConvertToWorkOrderPayload,
    MaintenanceDowntimeCreate,
    MaintenanceDowntimeRead,
    MaintenanceFailureAnalysisReportRead,
    MaintenanceFindingCreateRequestPayload,
    MaintenanceFindingRead,
    MaintenanceLaborLogCreate,
    MaintenanceMasterCodeCreate,
    MaintenanceMasterCodeRead,
    MaintenancePartUsageCreate,
    MaintenancePlanAssetCreate,
    MaintenancePlanCreate,
    MaintenancePlanGeneratePayload,
    MaintenancePlanListItemRead,
    MaintenancePlanRead,
    MaintenancePriorityCreate,
    MaintenancePriorityRead,
    MaintenanceReliabilityReportRead,
    MaintenanceRequestActionPayload,
    MaintenanceRequestCreate,
    MaintenanceRequestListItemRead,
    MaintenanceRequestRead,
    MaintenanceRequestRejectPayload,
    MaintenanceRequestTriagePayload,
    MaintenanceScheduleConfirmPayload,
    MaintenanceScheduleCreate,
    MaintenanceScheduleListItemRead,
    MaintenanceScheduleRead,
    MaintenanceScheduleReschedulePayload,
    MaintenanceSlaReportRead,
    MaintenanceTeamCreate,
    MaintenanceTeamListItemRead,
    MaintenanceTeamMemberCreate,
    MaintenanceTeamRead,
    MaintenanceWorkOrderAssignPayload,
    MaintenanceWorkOrderCompletePayload,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderEventRead,
    MaintenanceWorkOrderListItemRead,
    MaintenanceWorkOrderRead,
    MaintenanceWorkOrderVerifyPayload,
)
from app.modules.maintenance.service import MaintenanceService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter(prefix="/maintenance")


@router.post(
    "/priorities",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_priority(
    request: Request,
    payload: MaintenancePriorityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_priority(payload)
    return success_response(
        request=request,
        message="Maintenance priority berhasil dibuat.",
        data=MaintenancePriorityRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/priorities", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_priorities(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.list_priorities()
    return success_response(
        request=request,
        message="Daftar maintenance priority berhasil diambil.",
        data=[
            MaintenancePriorityRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/symptom-codes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_symptom_code(
    request: Request,
    payload: MaintenanceMasterCodeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_symptom_code(payload)
    return success_response(
        request=request,
        message="Maintenance symptom code berhasil dibuat.",
        data=MaintenanceMasterCodeRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/symptom-codes", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_symptom_codes(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.list_symptom_codes()
    return success_response(
        request=request,
        message="Daftar maintenance symptom code berhasil diambil.",
        data=[
            MaintenanceMasterCodeRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/failure-modes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_failure_mode(
    request: Request,
    payload: MaintenanceMasterCodeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_failure_mode(payload)
    return success_response(
        request=request,
        message="Maintenance failure mode berhasil dibuat.",
        data=MaintenanceMasterCodeRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/failure-modes", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_failure_modes(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.list_failure_modes()
    return success_response(
        request=request,
        message="Daftar maintenance failure mode berhasil diambil.",
        data=[
            MaintenanceMasterCodeRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/root-cause-codes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_root_cause_code(
    request: Request,
    payload: MaintenanceMasterCodeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_root_cause_code(payload)
    return success_response(
        request=request,
        message="Maintenance root cause code berhasil dibuat.",
        data=MaintenanceMasterCodeRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/root-cause-codes", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_root_cause_codes(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.list_root_cause_codes()
    return success_response(
        request=request,
        message="Daftar maintenance root cause code berhasil diambil.",
        data=[
            MaintenanceMasterCodeRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/checklist-templates",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_checklist_template(
    request: Request,
    payload: MaintenanceChecklistTemplateCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_checklist_template(payload)
    return success_response(
        request=request,
        message="Maintenance checklist template berhasil dibuat.",
        data=MaintenanceChecklistTemplateRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/checklist-templates/{template_id}",
    dependencies=[Depends(require_maintenance_read)],
)
async def get_maintenance_checklist_template(
    request: Request,
    template_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_checklist_template(template_id)
    return success_response(
        request=request,
        message="Detail maintenance checklist template berhasil diambil.",
        data=MaintenanceChecklistTemplateRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/plans",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_plan(
    request: Request,
    payload: MaintenancePlanCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_plan(payload)
    return success_response(
        request=request,
        message="Maintenance plan berhasil dibuat.",
        data=MaintenancePlanRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/plans", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_plans(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(default="plan_code", pattern="^(plan_code|plan_name|maintenance_type)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_plans(pagination)
    return success_response(
        request=request,
        message="Daftar maintenance plan berhasil diambil.",
        data=[
            MaintenancePlanListItemRead.from_model(item).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/plans/{plan_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_plan(
    request: Request,
    plan_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_plan(plan_id)
    return success_response(
        request=request,
        message="Detail maintenance plan berhasil diambil.",
        data=MaintenancePlanRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/plans/{plan_id}/assets",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def add_maintenance_plan_asset(
    request: Request,
    plan_id: UUID,
    payload: MaintenancePlanAssetCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.add_plan_asset(plan_id, payload)
    return success_response(
        request=request,
        message="Asset target maintenance plan berhasil ditambahkan.",
        data=MaintenancePlanRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/plans/{plan_id}/generate",
    dependencies=[Depends(require_maintenance_write)],
)
async def generate_maintenance_plan_schedules(
    request: Request,
    plan_id: UUID,
    payload: MaintenancePlanGeneratePayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.generate_schedules_from_plan(plan_id, payload)
    return success_response(
        request=request,
        message="Schedule dari maintenance plan berhasil digenerate.",
        data=[
            MaintenanceScheduleRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/teams",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_team(
    request: Request,
    payload: MaintenanceTeamCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_team(payload)
    return success_response(
        request=request,
        message="Maintenance team berhasil dibuat.",
        data=MaintenanceTeamRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/teams", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_teams(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(default="team_code", pattern="^(team_code|team_name|team_type)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_teams(pagination)
    return success_response(
        request=request,
        message="Daftar maintenance team berhasil diambil.",
        data=[
            MaintenanceTeamListItemRead.from_model(item).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/teams/{team_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_team(
    request: Request,
    team_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_team(team_id)
    return success_response(
        request=request,
        message="Detail maintenance team berhasil diambil.",
        data=MaintenanceTeamRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/teams/{team_id}/members",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def add_maintenance_team_member(
    request: Request,
    team_id: UUID,
    payload: MaintenanceTeamMemberCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.add_team_member(team_id, payload)
    return success_response(
        request=request,
        message="Member maintenance team berhasil ditambahkan.",
        data=MaintenanceTeamRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/requests",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_request(
    request: Request,
    payload: MaintenanceRequestCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_request(payload)
    return success_response(
        request=request,
        message="Maintenance request berhasil dibuat.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/requests", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_requests(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(default="reported_at", pattern="^(request_number|reported_at|status|title)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_requests(pagination)
    return success_response(
        request=request,
        message="Daftar maintenance request berhasil diambil.",
        data=[
            MaintenanceRequestListItemRead.from_model(item).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/requests/{request_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_request(
    request: Request,
    request_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_request(request_id)
    return success_response(
        request=request,
        message="Detail maintenance request berhasil diambil.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/requests/{request_id}/submit",
    dependencies=[Depends(require_maintenance_write)],
)
async def submit_maintenance_request(
    request: Request,
    request_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.submit_request(request_id, payload)
    return success_response(
        request=request,
        message="Maintenance request berhasil disubmit.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/requests/{request_id}/triage",
    dependencies=[Depends(require_maintenance_write)],
)
async def triage_maintenance_request(
    request: Request,
    request_id: UUID,
    payload: MaintenanceRequestTriagePayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.triage_request(request_id, payload)
    return success_response(
        request=request,
        message="Maintenance request berhasil ditriage.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/requests/{request_id}/approve",
    dependencies=[Depends(require_maintenance_write)],
)
async def approve_maintenance_request(
    request: Request,
    request_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.approve_request(request_id, payload)
    return success_response(
        request=request,
        message="Maintenance request berhasil diapprove.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/requests/{request_id}/reject",
    dependencies=[Depends(require_maintenance_write)],
)
async def reject_maintenance_request(
    request: Request,
    request_id: UUID,
    payload: MaintenanceRequestRejectPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.reject_request(request_id, payload)
    return success_response(
        request=request,
        message="Maintenance request berhasil direject.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/requests/{request_id}/convert-to-work-order",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def convert_request_to_work_order(
    request: Request,
    request_id: UUID,
    payload: MaintenanceConvertToWorkOrderPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.convert_request_to_work_order(request_id, payload)
    return success_response(
        request=request,
        message="Maintenance request berhasil dikonversi menjadi work order.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/requests/{request_id}/attachments",
    dependencies=[Depends(require_maintenance_read)],
)
async def list_maintenance_request_attachments(
    request: Request,
    request_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_entity_attachments(
        entity_type=AttachmentEntityType.MAINTENANCE_REQUEST.value,
        entity_id=request_id,
    )
    return success_response(
        request=request,
        message="Daftar attachment maintenance request berhasil diambil.",
        data=[
            AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in items
        ],
    )


@router.post(
    "/requests/{request_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_request_attachment(
    request: Request,
    request_id: UUID,
    payload: AttachmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    enriched_payload = payload.model_copy(
        update={
            "entity_type": AttachmentEntityType.MAINTENANCE_REQUEST,
            "entity_id": request_id,
        }
    )
    item = await service.create_attachment(enriched_payload)
    return success_response(
        request=request,
        message="Attachment maintenance request berhasil dibuat.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get(
    "/work-orders/{work_order_id}/attachments",
    dependencies=[Depends(require_maintenance_read)],
)
async def list_maintenance_work_order_attachments(
    request: Request,
    work_order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_entity_attachments(
        entity_type=AttachmentEntityType.MAINTENANCE_WORK_ORDER.value,
        entity_id=work_order_id,
    )
    return success_response(
        request=request,
        message="Daftar attachment maintenance work order berhasil diambil.",
        data=[
            AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in items
        ],
    )


@router.post(
    "/work-orders/{work_order_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_work_order_attachment(
    request: Request,
    work_order_id: UUID,
    payload: AttachmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    enriched_payload = payload.model_copy(
        update={
            "entity_type": AttachmentEntityType.MAINTENANCE_WORK_ORDER,
            "entity_id": work_order_id,
        }
    )
    item = await service.create_attachment(enriched_payload)
    return success_response(
        request=request,
        message="Attachment maintenance work order berhasil dibuat.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.post(
    "/work-orders",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_work_order(
    request: Request,
    payload: MaintenanceWorkOrderCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_work_order(payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil dibuat.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/work-orders", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_work_orders(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="created_at",
        pattern="^(work_order_number|created_at|status|planned_start_at|actual_start_at)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_work_orders(pagination)
    return success_response(
        request=request,
        message="Daftar maintenance work order berhasil diambil.",
        data=[
            MaintenanceWorkOrderListItemRead.from_model(item).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/work-orders/{work_order_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_work_order(work_order_id)
    return success_response(
        request=request,
        message="Detail maintenance work order berhasil diambil.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/approve",
    dependencies=[Depends(require_maintenance_write)],
)
async def approve_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.approve_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil diapprove.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/assign",
    dependencies=[Depends(require_maintenance_write)],
)
async def assign_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceWorkOrderAssignPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.assign_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil di-assign.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/start",
    dependencies=[Depends(require_maintenance_write)],
)
async def start_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.start_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil dimulai.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/hold",
    dependencies=[Depends(require_maintenance_write)],
)
async def hold_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.hold_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil di-hold.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/resume",
    dependencies=[Depends(require_maintenance_write)],
)
async def resume_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.resume_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil dilanjutkan.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/cancel",
    dependencies=[Depends(require_maintenance_write)],
)
async def cancel_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.cancel_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil dibatalkan.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/complete",
    dependencies=[Depends(require_maintenance_write)],
)
async def complete_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceWorkOrderCompletePayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.complete_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil diselesaikan.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/verify",
    dependencies=[Depends(require_maintenance_write)],
)
async def verify_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceWorkOrderVerifyPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.verify_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil diverifikasi.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/close",
    dependencies=[Depends(require_maintenance_write)],
)
async def close_maintenance_work_order(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceRequestActionPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.close_work_order(work_order_id, payload)
    return success_response(
        request=request,
        message="Maintenance work order berhasil ditutup.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/checklists",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def start_maintenance_work_order_checklist(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceChecklistExecutionStartPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.start_work_order_checklist(work_order_id, payload)
    return success_response(
        request=request,
        message="Checklist execution maintenance berhasil dimulai.",
        data=MaintenanceChecklistExecutionRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/parts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_work_order_part_usage(
    request: Request,
    work_order_id: UUID,
    payload: MaintenancePartUsageCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_part_usage(work_order_id, payload)
    return success_response(
        request=request,
        message="Part usage maintenance work order berhasil dicatat.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/labor-logs",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_work_order_labor_log(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceLaborLogCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_labor_log(work_order_id, payload)
    return success_response(
        request=request,
        message="Labor log maintenance work order berhasil dicatat.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/work-orders/{work_order_id}/downtimes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_work_order_downtime(
    request: Request,
    work_order_id: UUID,
    payload: MaintenanceDowntimeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_downtime(work_order_id, payload)
    return success_response(
        request=request,
        message="Downtime maintenance work order berhasil dicatat.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/work-orders/{work_order_id}/downtimes",
    dependencies=[Depends(require_maintenance_read)],
)
async def list_maintenance_work_order_downtimes(
    request: Request,
    work_order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.list_downtimes(work_order_id)
    return success_response(
        request=request,
        message="Daftar downtime maintenance work order berhasil diambil.",
        data=[
            MaintenanceDowntimeRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post(
    "/work-orders/{work_order_id}/failures",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_work_order_failure(
    request: Request,
    work_order_id: UUID,
    payload: AssetFailureCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_failure(
        work_order_id,
        payload.model_copy(
            update={
                "created_by": current_user.id,
                "detected_by_employee_id": payload.detected_by_employee_id or current_user.id,
            }
        ),
    )
    return success_response(
        request=request,
        message="Asset failure berhasil dicatat pada work order.",
        data=MaintenanceWorkOrderRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/failures", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_failures(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="detected_at",
        pattern="^(failure_number|detected_at|failure_severity|status|created_at)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    asset_id: UUID | None = None,
    work_order_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    failure_mode_id: UUID | None = None,
    root_cause_code_id: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    items, total_items = await service.list_failures(
        pagination,
        asset_id=asset_id,
        work_order_id=work_order_id,
        status=status_filter,
        failure_mode_id=failure_mode_id,
        root_cause_code_id=root_cause_code_id,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )
    return success_response(
        request=request,
        message="Daftar asset failure berhasil diambil.",
        data=[AssetFailureListItemRead.from_model(item).model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/failures/{failure_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_failure(
    request: Request,
    failure_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_failure(failure_id)
    return success_response(
        request=request,
        message="Detail asset failure berhasil diambil.",
        data=AssetFailureRead.model_validate(item).model_dump(mode="json"),
    )


@router.patch(
    "/failures/{failure_id}",
    dependencies=[Depends(require_maintenance_write)],
)
async def update_maintenance_failure(
    request: Request,
    failure_id: UUID,
    payload: AssetFailureUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.update_failure(
        failure_id,
        payload,
        actor_id=current_user.id,
    )
    return success_response(
        request=request,
        message="Asset failure berhasil diperbarui.",
        data=AssetFailureRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/work-orders/{work_order_id}/events",
    dependencies=[Depends(require_maintenance_read)],
)
async def list_maintenance_work_order_events(
    request: Request,
    work_order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    items = await service.list_work_order_events(work_order_id)
    return success_response(
        request=request,
        message="Daftar event maintenance work order berhasil diambil.",
        data=[
            MaintenanceWorkOrderEventRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.get(
    "/reports/backlog",
    dependencies=[Depends(require_maintenance_report_read)],
)
async def get_maintenance_backlog_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_backlog_report()
    return success_response(
        request=request,
        message="Report backlog maintenance berhasil diambil.",
        data=item.model_dump(mode="json"),
    )


@router.get(
    "/reports/cost",
    dependencies=[Depends(require_maintenance_report_read)],
)
async def get_maintenance_cost_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="closed_at",
        pattern=(
            "^(work_order_number|maintenance_type|status|actual_end_at|closed_at|"
            "actual_part_cost|actual_labor_cost|actual_vendor_cost)$"
        ),
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    asset_id: UUID | None = None,
    maintenance_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    items, total_items = await service.get_cost_report(
        pagination,
        asset_id=asset_id,
        maintenance_type=maintenance_type,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )
    return success_response(
        request=request,
        message="Report biaya maintenance berhasil diambil.",
        data=[item.model_dump(mode="json") for item in items],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get(
    "/reports/sla",
    dependencies=[Depends(require_maintenance_report_read)],
)
async def get_maintenance_sla_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    service = MaintenanceService(session)
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    item = await service.get_sla_report(
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )
    return success_response(
        request=request,
        message="Report SLA maintenance berhasil diambil.",
        data=MaintenanceSlaReportRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/reports/reliability",
    dependencies=[Depends(require_maintenance_report_read)],
)
async def get_maintenance_reliability_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    service = MaintenanceService(session)
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    item = await service.get_reliability_report(
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )
    return success_response(
        request=request,
        message="Report reliability maintenance berhasil diambil.",
        data=MaintenanceReliabilityReportRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/reports/failure-analysis",
    dependencies=[Depends(require_maintenance_report_read)],
)
async def get_maintenance_failure_analysis_report(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    asset_id: UUID | None = None,
    failure_mode_id: UUID | None = None,
    root_cause_code_id: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    service = MaintenanceService(session)
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    item = await service.get_failure_analysis_report(
        asset_id=asset_id,
        failure_mode_id=failure_mode_id,
        root_cause_code_id=root_cause_code_id,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )
    return success_response(
        request=request,
        message="Report failure analysis maintenance berhasil diambil.",
        data=MaintenanceFailureAnalysisReportRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/checklists/{checklist_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_checklist_execution(
    request: Request,
    checklist_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_checklist_execution(checklist_id)
    return success_response(
        request=request,
        message="Detail checklist execution maintenance berhasil diambil.",
        data=MaintenanceChecklistExecutionRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/checklists/{checklist_id}/results",
    dependencies=[Depends(require_maintenance_write)],
)
async def submit_maintenance_checklist_results(
    request: Request,
    checklist_id: UUID,
    payload: MaintenanceChecklistResultSubmitPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.submit_checklist_results(checklist_id, payload)
    return success_response(
        request=request,
        message="Hasil checklist maintenance berhasil disimpan.",
        data=MaintenanceChecklistExecutionRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/findings/{finding_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_finding(
    request: Request,
    finding_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_finding(finding_id)
    return success_response(
        request=request,
        message="Detail maintenance finding berhasil diambil.",
        data=MaintenanceFindingRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/findings/{finding_id}/create-request",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_request_from_maintenance_finding(
    request: Request,
    finding_id: UUID,
    payload: MaintenanceFindingCreateRequestPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_request_from_finding(finding_id, payload)
    return success_response(
        request=request,
        message="Follow-up request dari maintenance finding berhasil dibuat.",
        data=MaintenanceRequestRead.model_validate(item).model_dump(mode="json"),
    )


@router.get(
    "/findings/{finding_id}/attachments",
    dependencies=[Depends(require_maintenance_read)],
)
async def list_maintenance_finding_attachments(
    request: Request,
    finding_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_entity_attachments(
        entity_type=AttachmentEntityType.MAINTENANCE_FINDING.value,
        entity_id=finding_id,
    )
    return success_response(
        request=request,
        message="Daftar attachment maintenance finding berhasil diambil.",
        data=[
            AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in items
        ],
    )


@router.post(
    "/findings/{finding_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_finding_attachment(
    request: Request,
    finding_id: UUID,
    payload: AttachmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    enriched_payload = payload.model_copy(
        update={
            "entity_type": AttachmentEntityType.MAINTENANCE_FINDING,
            "entity_id": finding_id,
        }
    )
    item = await service.create_attachment(enriched_payload)
    return success_response(
        request=request,
        message="Attachment maintenance finding berhasil dibuat.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.get(
    "/failures/{failure_id}/attachments",
    dependencies=[Depends(require_maintenance_read)],
)
async def list_maintenance_failure_attachments(
    request: Request,
    failure_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AttachmentService(session)
    items = await service.list_entity_attachments(
        entity_type=AttachmentEntityType.ASSET_FAILURE.value,
        entity_id=failure_id,
    )
    return success_response(
        request=request,
        message="Daftar attachment asset failure berhasil diambil.",
        data=[
            AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True)
            for item in items
        ],
    )


@router.post(
    "/failures/{failure_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_failure_attachment(
    request: Request,
    failure_id: UUID,
    payload: AttachmentCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> dict:
    service = AttachmentService(session)
    enriched_payload = payload.model_copy(
        update={
            "entity_type": AttachmentEntityType.ASSET_FAILURE,
            "entity_id": failure_id,
            "created_by": current_user.id,
            "captured_by": payload.captured_by or current_user.id,
            "file": payload.file.model_copy(update={"uploaded_by": current_user.id}),
        }
    )
    item = await service.create_attachment(enriched_payload)
    return success_response(
        request=request,
        message="Attachment asset failure berhasil dibuat.",
        data=AttachmentRead.model_validate(item).model_dump(mode="json", by_alias=True),
    )


@router.post(
    "/schedules",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_write)],
)
async def create_maintenance_schedule(
    request: Request,
    payload: MaintenanceScheduleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.create_schedule(payload)
    return success_response(
        request=request,
        message="Maintenance schedule berhasil dibuat.",
        data=MaintenanceScheduleRead.model_validate(item).model_dump(mode="json"),
    )


@router.get("/schedules", dependencies=[Depends(require_maintenance_read)])
async def list_maintenance_schedules(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query(
        default="scheduled_start_at",
        pattern="^(schedule_number|scheduled_start_at|scheduled_end_at|status)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict:
    service = MaintenanceService(session)
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    items, total_items = await service.list_schedules(pagination)
    return success_response(
        request=request,
        message="Daftar maintenance schedule berhasil diambil.",
        data=[
            MaintenanceScheduleListItemRead.from_model(item).model_dump(mode="json")
            for item in items
        ],
        pagination=PaginationMeta.create(page=page, page_size=page_size, total_items=total_items),
    )


@router.get("/schedules/{schedule_id}", dependencies=[Depends(require_maintenance_read)])
async def get_maintenance_schedule(
    request: Request,
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.get_schedule(schedule_id)
    return success_response(
        request=request,
        message="Detail maintenance schedule berhasil diambil.",
        data=MaintenanceScheduleRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/schedules/{schedule_id}/confirm",
    dependencies=[Depends(require_maintenance_write)],
)
async def confirm_maintenance_schedule(
    request: Request,
    schedule_id: UUID,
    payload: MaintenanceScheduleConfirmPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.confirm_schedule(schedule_id, payload)
    return success_response(
        request=request,
        message="Maintenance schedule berhasil dikonfirmasi.",
        data=MaintenanceScheduleRead.model_validate(item).model_dump(mode="json"),
    )


@router.post(
    "/schedules/{schedule_id}/reschedule",
    dependencies=[Depends(require_maintenance_write)],
)
async def reschedule_maintenance_schedule(
    request: Request,
    schedule_id: UUID,
    payload: MaintenanceScheduleReschedulePayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = MaintenanceService(session)
    item = await service.reschedule(schedule_id, payload)
    return success_response(
        request=request,
        message="Maintenance schedule berhasil di-reschedule.",
        data=MaintenanceScheduleRead.model_validate(item).model_dump(mode="json"),
    )
