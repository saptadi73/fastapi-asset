from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import AppError
from app.modules.auth.models import AppUser, AuthRefreshToken, AuthTokenFamily
from app.modules.auth.schemas import AuthLoginRequest, AuthRefreshRequest
from app.modules.auth.service import AuthService


class FakeSession:
    @asynccontextmanager
    async def begin(self):
        yield

    async def commit(self) -> None:
        return None


class FakeUserRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, AppUser] = {}

    async def create(self, item: AppUser) -> AppUser:
        if item.id is None:
            item.id = uuid4()
        self.items[item.id] = item
        return item

    async def get(self, user_id: UUID) -> AppUser | None:
        return self.items.get(user_id)

    async def get_by_email(self, email: str) -> AppUser | None:
        for item in self.items.values():
            if item.email == email:
                return item
        return None

    async def count_all(self) -> int:
        return len(self.items)

    async def update(self, item: AppUser, **changes: object) -> AppUser:
        for key, value in changes.items():
            setattr(item, key, value)
        return item


class FakeTokenFamilyRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, AuthTokenFamily] = {}

    async def create(self, item: AuthTokenFamily) -> AuthTokenFamily:
        if item.id is None:
            item.id = uuid4()
        self.items[item.id] = item
        return item

    async def get(self, family_id: UUID) -> AuthTokenFamily | None:
        return self.items.get(family_id)

    async def update(self, item: AuthTokenFamily, **changes: object) -> AuthTokenFamily:
        for key, value in changes.items():
            setattr(item, key, value)
        return item

    async def list_by_user(self, user_id: UUID):
        return [item for item in self.items.values() if item.user_id == user_id]


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self.items: dict[str, AuthRefreshToken] = {}

    async def create(self, item: AuthRefreshToken) -> AuthRefreshToken:
        if item.id is None:
            item.id = uuid4()
        self.items[item.jti] = item
        return item

    async def get_by_jti(self, jti: str) -> AuthRefreshToken | None:
        return self.items.get(jti)

    async def list_by_family(self, family_id: UUID):
        return [item for item in self.items.values() if item.family_id == family_id]

    async def update(self, item: AuthRefreshToken, **changes: object) -> AuthRefreshToken:
        for key, value in changes.items():
            setattr(item, key, value)
        return item


@pytest.fixture
def service() -> AuthService:
    svc = AuthService(FakeSession())
    svc.users = FakeUserRepository()
    svc.token_families = FakeTokenFamilyRepository()
    svc.refresh_tokens = FakeRefreshTokenRepository()
    return svc


@pytest.mark.asyncio
async def test_login_issues_tokens_and_current_user_resolves(service: AuthService) -> None:
    user = AppUser(
        email="admin@example.com",
        full_name="Admin",
        password_hash=service.hash_password("Secret123!"),
        is_active=True,
        is_superuser=True,
        roles=["SUPERUSER"],
        permissions=["*"],
    )
    await service.users.create(user)

    session = await service.login(
        AuthLoginRequest(email="admin@example.com", password="Secret123!")
    )
    auth = await service.get_current_user(session.tokens.access_token)

    assert session.user.email == "admin@example.com"
    assert session.tokens.token_type == "Bearer"
    assert auth.user.id == user.id
    assert auth.family is not None


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_reuse_revokes_family(service: AuthService) -> None:
    user = AppUser(
        email="planner@example.com",
        full_name="Planner",
        password_hash=service.hash_password("Secret123!"),
        is_active=True,
        is_superuser=False,
        roles=["MAINTENANCE_PLANNER"],
        permissions=["maintenance:read"],
        last_login_at=datetime.now(UTC) - timedelta(hours=1),
    )
    await service.users.create(user)

    session = await service.login(
        AuthLoginRequest(email="planner@example.com", password="Secret123!")
    )
    refreshed = await service.refresh(
        AuthRefreshRequest(refresh_token=session.tokens.refresh_token)
    )

    assert refreshed.refresh_token != session.tokens.refresh_token
    assert refreshed.access_token != session.tokens.access_token

    with pytest.raises(AppError) as exc_info:
        await service.refresh(AuthRefreshRequest(refresh_token=session.tokens.refresh_token))

    assert exc_info.value.code == "AUTH_REFRESH_TOKEN_REUSED"

    with pytest.raises(AppError) as access_exc:
        await service.get_current_user(refreshed.access_token)

    assert access_exc.value.code == "AUTH_SESSION_REVOKED"
