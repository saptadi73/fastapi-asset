from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import AppUser, AuthRefreshToken, AuthTokenFamily


class AppUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AppUser) -> AppUser:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, user_id: UUID) -> AppUser | None:
        return await self.session.get(AppUser, user_id)

    async def get_by_email(self, email: str) -> AppUser | None:
        stmt = select(AppUser).where(AppUser.email == email.lower())
        return await self.session.scalar(stmt)

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(AppUser)
        return await self.session.scalar(stmt) or 0

    async def update(self, item: AppUser, **changes: object) -> AppUser:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        return item


class AuthTokenFamilyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AuthTokenFamily) -> AuthTokenFamily:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, family_id: UUID) -> AuthTokenFamily | None:
        stmt = (
            select(AuthTokenFamily)
            .options(selectinload(AuthTokenFamily.user))
            .where(AuthTokenFamily.id == family_id)
        )
        return await self.session.scalar(stmt)

    async def update(self, item: AuthTokenFamily, **changes: object) -> AuthTokenFamily:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        return item

    async def list_by_user(self, user_id: UUID) -> Sequence[AuthTokenFamily]:
        stmt = select(AuthTokenFamily).where(AuthTokenFamily.user_id == user_id)
        result = await self.session.scalars(stmt)
        return result.all()


class AuthRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: AuthRefreshToken) -> AuthRefreshToken:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_jti(self, jti: str) -> AuthRefreshToken | None:
        stmt = (
            select(AuthRefreshToken)
            .options(
                selectinload(AuthRefreshToken.user),
                selectinload(AuthRefreshToken.family),
            )
            .where(AuthRefreshToken.jti == jti)
        )
        return await self.session.scalar(stmt)

    async def list_by_family(self, family_id: UUID) -> Sequence[AuthRefreshToken]:
        stmt = select(AuthRefreshToken).where(AuthRefreshToken.family_id == family_id)
        result = await self.session.scalars(stmt)
        return result.all()

    async def update(self, item: AuthRefreshToken, **changes: object) -> AuthRefreshToken:
        for key, value in changes.items():
            setattr(item, key, value)
        await self.session.flush()
        return item
