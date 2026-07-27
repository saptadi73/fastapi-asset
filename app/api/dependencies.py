from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import AppError
from app.modules.auth.constants import AppPermission, AppRole
from app.modules.auth.models import AppUser
from app.modules.auth.service import AuthContext, AuthService


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_auth_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="AUTH_TOKEN_REQUIRED",
            message="Bearer token diperlukan.",
            status_code=401,
        )
    service = AuthService(session)
    return await service.get_current_user(credentials.credentials)


async def get_current_user(
    auth: Annotated[AuthContext, Depends(get_current_auth_context)],
) -> AppUser:
    return auth.user


def require_permissions(*required_permissions: str):
    async def dependency(
        user: Annotated[AppUser, Depends(get_current_user)],
    ) -> AppUser:
        if user.is_superuser or "*" in user.permissions:
            return user
        missing = [
            permission for permission in required_permissions if permission not in user.permissions
        ]
        if missing:
            raise AppError(
                code="AUTH_PERMISSION_DENIED",
                message="User tidak memiliki permission yang diperlukan.",
                status_code=403,
                details={"required_permissions": list(required_permissions)},
            )
        return user

    return dependency


def require_roles(*required_roles: str):
    async def dependency(
        user: Annotated[AppUser, Depends(get_current_user)],
    ) -> AppUser:
        if user.is_superuser or AppRole.SUPERUSER.value in user.roles:
            return user
        if not any(role in user.roles for role in required_roles):
            raise AppError(
                code="AUTH_ROLE_DENIED",
                message="User tidak memiliki role yang diperlukan.",
                status_code=403,
                details={"required_roles": list(required_roles)},
            )
        return user

    return dependency


require_maintenance_read = require_permissions(AppPermission.MAINTENANCE_READ.value)
require_maintenance_write = require_permissions(AppPermission.MAINTENANCE_WRITE.value)
require_maintenance_report_read = require_permissions(
    AppPermission.MAINTENANCE_REPORT_READ.value
)
