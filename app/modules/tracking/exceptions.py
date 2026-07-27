from fastapi import status

from app.core.exceptions import AppError


class AssetScanEventNotFoundError(AppError):
    def __init__(self, scan_event_id: str) -> None:
        super().__init__(
            code="ASSET_SCAN_EVENT_NOT_FOUND",
            message="Asset scan event tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"scan_event_id": scan_event_id},
        )


class StocktakeSessionNotFoundError(AppError):
    def __init__(self, stocktake_session_id: str) -> None:
        super().__init__(
            code="STOCKTAKE_SESSION_NOT_FOUND",
            message="Stocktake session tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"stocktake_session_id": stocktake_session_id},
        )
