from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


def _meta(request: Request) -> dict[str, object]:
    return {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": datetime.now(UTC).isoformat(),
        "api_version": "v1",
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "meta": _meta(request),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Permintaan tidak valid.",
                "data": None,
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "Permintaan tidak valid.",
                    "details": exc.errors(),
                },
                "meta": _meta(request),
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Terjadi kesalahan internal.",
                "data": None,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Terjadi kesalahan internal.",
                    "details": None,
                },
                "meta": _meta(request),
            },
        )
