from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from pydantic import BaseModel, ConfigDict

from app.shared.pagination import PaginationMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | dict[str, Any] | None = None


class ResponseMeta(BaseModel):
    request_id: str | None
    timestamp: datetime
    api_version: str
    pagination: PaginationMeta | None = None


class ApiResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    message: str
    data: Any = None
    error: ErrorDetail | None = None
    meta: ResponseMeta


def build_meta(request: Request, pagination: PaginationMeta | None = None) -> ResponseMeta:
    return ResponseMeta(
        request_id=getattr(request.state, "request_id", None),
        timestamp=datetime.now(UTC),
        api_version="v1",
        pagination=pagination,
    )


def success_response(
    *,
    request: Request,
    message: str,
    data: Any = None,
    pagination: PaginationMeta | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
        "meta": build_meta(request, pagination).model_dump(mode="json"),
    }
