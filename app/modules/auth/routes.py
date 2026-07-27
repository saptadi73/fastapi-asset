from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth_context, get_session
from app.modules.auth.schemas import (
    AuthLoginRequest,
    AuthRefreshRequest,
    AuthSessionRead,
    AuthTokenPairRead,
    AuthUserRead,
)
from app.modules.auth.service import AuthContext, AuthService
from app.shared.responses import success_response

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(
    request: Request,
    payload: AuthLoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AuthService(session)
    item = await service.login(payload)
    return success_response(
        request=request,
        message="Login berhasil.",
        data=AuthSessionRead.model_validate(item).model_dump(mode="json"),
    )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    payload: AuthRefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AuthService(session)
    item = await service.refresh(payload)
    return success_response(
        request=request,
        message="Refresh token berhasil diputar.",
        data=AuthTokenPairRead.model_validate(item).model_dump(mode="json"),
    )


@router.post("/logout")
async def logout(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    service = AuthService(session)
    await service.logout(auth)
    return success_response(
        request=request,
        message="Logout berhasil.",
        data={"logged_out": True},
    )


@router.get("/me")
async def get_me(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth_context)],
) -> dict:
    return success_response(
        request=request,
        message="Profil user berhasil diambil.",
        data=AuthUserRead.model_validate(auth.user).model_dump(mode="json"),
    )
