from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.modules.attachments.constants import AttachmentEntityType
from app.modules.attachments.schemas import AttachmentCreate, AttachmentRead
from app.modules.attachments.service import AttachmentService
from app.modules.maintenance.schemas import (
    MaintenanceConvertToWorkOrderPayload,
    MaintenancePlanAssetCreate,
    MaintenancePlanCreate,
    MaintenancePlanGeneratePayload,
    MaintenancePlanListItemRead,
    MaintenancePlanRead,
    MaintenancePriorityCreate,
    MaintenancePriorityRead,
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
    MaintenanceTeamCreate,
    MaintenanceTeamListItemRead,
    MaintenanceTeamMemberCreate,
    MaintenanceTeamRead,
    MaintenanceWorkOrderAssignPayload,
    MaintenanceWorkOrderCompletePayload,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderListItemRead,
    MaintenanceWorkOrderRead,
    MaintenanceWorkOrderVerifyPayload,
)
from app.modules.maintenance.service import MaintenanceService
from app.shared.pagination import PaginationMeta, PaginationParams
from app.shared.responses import success_response

router = APIRouter(prefix="/maintenance")


@router.post("/priorities", status_code=status.HTTP_201_CREATED)
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


@router.get("/priorities")
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


@router.post("/plans", status_code=status.HTTP_201_CREATED)
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


@router.get("/plans")
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


@router.get("/plans/{plan_id}")
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


@router.post("/plans/{plan_id}/assets", status_code=status.HTTP_201_CREATED)
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


@router.post("/plans/{plan_id}/generate")
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


@router.post("/teams", status_code=status.HTTP_201_CREATED)
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


@router.get("/teams")
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


@router.get("/teams/{team_id}")
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


@router.post("/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
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


@router.post("/requests", status_code=status.HTTP_201_CREATED)
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


@router.get("/requests")
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


@router.get("/requests/{request_id}")
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


@router.post("/requests/{request_id}/submit")
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


@router.post("/requests/{request_id}/triage")
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


@router.post("/requests/{request_id}/approve")
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


@router.post("/requests/{request_id}/reject")
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


@router.post("/requests/{request_id}/convert-to-work-order", status_code=status.HTTP_201_CREATED)
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


@router.get("/requests/{request_id}/attachments")
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


@router.post("/requests/{request_id}/attachments", status_code=status.HTTP_201_CREATED)
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


@router.get("/work-orders/{work_order_id}/attachments")
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


@router.post("/work-orders/{work_order_id}/attachments", status_code=status.HTTP_201_CREATED)
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


@router.post("/work-orders", status_code=status.HTTP_201_CREATED)
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


@router.get("/work-orders")
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


@router.get("/work-orders/{work_order_id}")
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


@router.post("/work-orders/{work_order_id}/approve")
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


@router.post("/work-orders/{work_order_id}/assign")
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


@router.post("/work-orders/{work_order_id}/start")
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


@router.post("/work-orders/{work_order_id}/complete")
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


@router.post("/work-orders/{work_order_id}/verify")
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


@router.post("/work-orders/{work_order_id}/close")
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


@router.post("/schedules", status_code=status.HTTP_201_CREATED)
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


@router.get("/schedules")
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


@router.get("/schedules/{schedule_id}")
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


@router.post("/schedules/{schedule_id}/confirm")
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


@router.post("/schedules/{schedule_id}/reschedule")
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
