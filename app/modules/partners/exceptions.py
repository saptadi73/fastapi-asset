from fastapi import status

from app.core.exceptions import AppError


class BusinessPartnerNotFoundError(AppError):
    def __init__(self, partner_id: str) -> None:
        super().__init__(
            code="BUSINESS_PARTNER_NOT_FOUND",
            message="Business partner tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"partner_id": partner_id},
        )
