from fastapi import status

from app.core.exceptions import AppError


class AssetCategoryNotFoundError(AppError):
    def __init__(self, category_id: str) -> None:
        super().__init__(
            code="ASSET_CATEGORY_NOT_FOUND",
            message="Asset category tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"asset_category_id": category_id},
        )


class AssetClassNotFoundError(AppError):
    def __init__(self, asset_class_id: str) -> None:
        super().__init__(
            code="ASSET_CLASS_NOT_FOUND",
            message="Asset class tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"asset_class_id": asset_class_id},
        )


class AssetNotFoundError(AppError):
    def __init__(self, asset_id: str) -> None:
        super().__init__(
            code="ASSET_NOT_FOUND",
            message="Asset tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"asset_id": asset_id},
        )


class AssetLocationNotFoundError(AppError):
    def __init__(self, location_id: str) -> None:
        super().__init__(
            code="ASSET_LOCATION_NOT_FOUND",
            message="Asset location tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"location_id": location_id},
        )


class AssetAttributeDefinitionNotFoundError(AppError):
    def __init__(self, definition_id: str) -> None:
        super().__init__(
            code="ASSET_ATTRIBUTE_DEFINITION_NOT_FOUND",
            message="Asset attribute definition tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"attribute_definition_id": definition_id},
        )


class AssetTransferNotFoundError(AppError):
    def __init__(self, transfer_id: str) -> None:
        super().__init__(
            code="ASSET_TRANSFER_NOT_FOUND",
            message="Asset transfer tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"transfer_id": transfer_id},
        )
