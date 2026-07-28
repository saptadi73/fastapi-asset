from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.shared.responses import success_response

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/db", status_code=status.HTTP_200_OK)
async def database_health_check(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return {
            "success": False,
            "message": "Koneksi database gagal.",
            "data": {
                "database": "down",
                "detail": str(exc.__class__.__name__),
            },
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database tidak dapat diakses.",
                "details": None,
            },
            "meta": success_response(
                request=request,
                message="Koneksi database gagal.",
            )["meta"],
        }

    return success_response(
        request=request,
        message="Koneksi database berhasil.",
        data={"database": "up"},
    )
