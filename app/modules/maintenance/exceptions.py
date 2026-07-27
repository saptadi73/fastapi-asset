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


class MaintenanceChecklistTemplateNotFoundError(AppError):
    def __init__(self, template_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_CHECKLIST_TEMPLATE_NOT_FOUND",
            message="Maintenance checklist template tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"template_id": template_id},
        )


class MaintenanceChecklistExecutionNotFoundError(AppError):
    def __init__(self, checklist_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_CHECKLIST_EXECUTION_NOT_FOUND",
            message="Maintenance checklist execution tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"checklist_id": checklist_id},
        )


class MaintenanceFindingNotFoundError(AppError):
    def __init__(self, finding_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_FINDING_NOT_FOUND",
            message="Maintenance finding tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"finding_id": finding_id},
        )


class MaintenanceSymptomCodeNotFoundError(AppError):
    def __init__(self, symptom_code_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_SYMPTOM_CODE_NOT_FOUND",
            message="Maintenance symptom code tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"symptom_code_id": symptom_code_id},
        )


class MaintenanceFailureModeNotFoundError(AppError):
    def __init__(self, failure_mode_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_FAILURE_MODE_NOT_FOUND",
            message="Maintenance failure mode tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"failure_mode_id": failure_mode_id},
        )


class MaintenanceRootCauseCodeNotFoundError(AppError):
    def __init__(self, root_cause_code_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_ROOT_CAUSE_CODE_NOT_FOUND",
            message="Maintenance root cause code tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"root_cause_code_id": root_cause_code_id},
        )


class MaintenanceAssetFailureNotFoundError(AppError):
    def __init__(self, failure_id: str) -> None:
        super().__init__(
            code="MAINTENANCE_ASSET_FAILURE_NOT_FOUND",
            message="Asset failure tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"failure_id": failure_id},
        )
