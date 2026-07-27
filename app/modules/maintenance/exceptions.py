from fastapi import status

from app.core.exceptions import AppError


class MaintenancePriorityNotFoundError(AppError):
    def __init__(self, priority_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_PRIORITY_NOT_FOUND",
            message="Maintenance priority tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"priority_id": priority_id},
        )


class MaintenanceRequestNotFoundError(AppError):
    def __init__(self, request_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_REQUEST_NOT_FOUND",
            message="Maintenance request tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"request_id": request_id},
        )


class MaintenanceWorkOrderNotFoundError(AppError):
    def __init__(self, work_order_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_WORK_ORDER_NOT_FOUND",
            message="Maintenance work order tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"work_order_id": work_order_id},
        )


class MaintenanceTeamNotFoundError(AppError):
    def __init__(self, team_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_TEAM_NOT_FOUND",
            message="Maintenance team tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"team_id": team_id},
        )


class MaintenanceScheduleNotFoundError(AppError):
    def __init__(self, schedule_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_SCHEDULE_NOT_FOUND",
            message="Maintenance schedule tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"schedule_id": schedule_id},
        )
