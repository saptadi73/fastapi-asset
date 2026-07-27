from fastapi import status

from app.core.exceptions import AppError


class AttachmentNotFoundError(AppError):
    def __init__(self, attachment_id: str) -> None:
        super().__init__(
            code="ATTACHMENT_NOT_FOUND",
            message="Attachment tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"attachment_id": attachment_id},
        )


class FileRecordNotFoundError(AppError):
    def __init__(self, file_id: str) -> None:
        super().__init__(
            code="FILE_RECORD_NOT_FOUND",
            message="File record tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"file_id": file_id},
        )
