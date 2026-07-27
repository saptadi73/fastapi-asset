from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.auth.models import AppUser, AuthRefreshToken, AuthTokenFamily
from app.modules.auth.repository import (
    AppUserRepository,
    AuthRefreshTokenRepository,
    AuthTokenFamilyRepository,
)
from app.modules.auth.schemas import (
    AuthLoginRequest,
    AuthRefreshRequest,
    AuthSessionRead,
    AuthTokenPairRead,
    AuthUserRead,
)

settings = get_settings()
password_hasher = PasswordHasher()


@dataclass(slots=True)
class AuthContext:
    user: AppUser
    token_claims: dict[str, object]
    family: AuthTokenFamily | None


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = AppUserRepository(session)
        self.token_families = AuthTokenFamilyRepository(session)
        self.refresh_tokens = AuthRefreshTokenRepository(session)

    async def login(self, payload: AuthLoginRequest) -> AuthSessionRead:
        normalized_email = payload.email.lower()
        user = await self.users.get_by_email(normalized_email)
        if user is None:
            user = await self._bootstrap_admin_if_allowed(normalized_email, payload.password)
        if user is None or not self._verify_password(payload.password, user.password_hash):
            raise AppError(
                code="AUTH_INVALID_CREDENTIALS",
                message="Email atau password tidak valid.",
                status_code=401,
            )
        if not user.is_active:
            raise AppError(
                code="AUTH_USER_INACTIVE",
                message="User tidak aktif.",
                status_code=403,
            )

        await self.users.update(user, last_login_at=datetime.now(UTC))
        tokens = await self._issue_token_pair(user)
        await self.session.commit()
        return AuthSessionRead(
            user=AuthUserRead.model_validate(user),
            tokens=tokens,
        )

    async def refresh(self, payload: AuthRefreshRequest) -> AuthTokenPairRead:
        claims = self._decode_token(payload.refresh_token, expected_type="refresh")
        token = await self.refresh_tokens.get_by_jti(str(claims["jti"]))
        if token is None:
            raise AppError(
                code="AUTH_REFRESH_TOKEN_INVALID",
                message="Refresh token tidak valid.",
                status_code=401,
            )

        now = datetime.now(UTC)
        hashed_token = self._hash_token(payload.refresh_token)
        if not hmac.compare_digest(token.token_hash, hashed_token):
            raise AppError(
                code="AUTH_REFRESH_TOKEN_INVALID",
                message="Refresh token tidak valid.",
                status_code=401,
            )

        family = token.family
        if family is None:
            family = await self.token_families.get(token.family_id)
        if family is None:
            raise AppError(
                code="AUTH_REFRESH_TOKEN_INVALID",
                message="Session token tidak ditemukan.",
                status_code=401,
            )
        if family.revoked_at is not None:
            raise AppError(
                code="AUTH_REFRESH_TOKEN_REVOKED",
                message="Session sudah dicabut.",
                status_code=401,
            )
        if token.revoked_at is not None or token.expires_at <= now:
            raise AppError(
                code="AUTH_REFRESH_TOKEN_REVOKED",
                message="Refresh token sudah tidak berlaku.",
                status_code=401,
            )
        if token.used_at is not None:
            await self._revoke_family(
                family,
                reason="Refresh token reuse detected.",
            )
            await self.session.commit()
            raise AppError(
                code="AUTH_REFRESH_TOKEN_REUSED",
                message="Refresh token reuse terdeteksi. Session dicabut.",
                status_code=401,
            )
        user = token.user
        if user is None:
            user = await self.users.get(token.user_id)
        if user is None or not user.is_active:
            raise AppError(
                code="AUTH_USER_INACTIVE",
                message="User tidak aktif.",
                status_code=403,
            )

        new_tokens = await self._issue_token_pair(user, family_id=family.id)
        new_refresh_claims = self._decode_token(
            new_tokens.refresh_token,
            expected_type="refresh",
        )
        await self.refresh_tokens.update(
            token,
            used_at=now,
            replaced_by_jti=str(new_refresh_claims["jti"]),
        )
        await self.session.commit()
        return new_tokens

    async def logout(self, auth: AuthContext) -> None:
        family_id = auth.token_claims.get("sid")
        if family_id is None:
            raise AppError(
                code="AUTH_SESSION_INVALID",
                message="Session token tidak memiliki family id.",
                status_code=401,
        )
        family = auth.family or await self.token_families.get(UUID(str(family_id)))
        if family is None:
            return
        await self._revoke_family(family, reason="User logout.")
        await self.session.commit()

    async def get_current_user(self, access_token: str) -> AuthContext:
        claims = self._decode_token(access_token, expected_type="access")
        user_id = UUID(str(claims["sub"]))
        user = await self.users.get(user_id)
        if user is None:
            raise AppError(
                code="AUTH_USER_NOT_FOUND",
                message="User tidak ditemukan.",
                status_code=401,
            )
        if not user.is_active:
            raise AppError(
                code="AUTH_USER_INACTIVE",
                message="User tidak aktif.",
                status_code=403,
            )

        family = None
        if claims.get("sid") is not None:
            family = await self.token_families.get(UUID(str(claims["sid"])))
            if family is None or family.revoked_at is not None:
                raise AppError(
                    code="AUTH_SESSION_REVOKED",
                    message="Session sudah tidak berlaku.",
                    status_code=401,
                )

        return AuthContext(user=user, token_claims=claims, family=family)

    async def _bootstrap_admin_if_allowed(self, email: str, password: str) -> AppUser | None:
        if not settings.auth_bootstrap_admin_email or not settings.auth_bootstrap_admin_password:
            return None
        if email != settings.auth_bootstrap_admin_email.lower():
            return None
        if password != settings.auth_bootstrap_admin_password:
            return None
        if await self.users.count_all() > 0:
            return None

        user = AppUser(
            email=email,
            full_name=settings.auth_bootstrap_admin_full_name,
            password_hash=self.hash_password(password),
            is_active=True,
            is_superuser=True,
            roles=["SUPERUSER"],
            permissions=["*"],
        )
        await self.users.create(user)
        return user

    async def _issue_token_pair(
        self,
        user: AppUser,
        *,
        family_id: UUID | None = None,
    ) -> AuthTokenPairRead:
        now = datetime.now(UTC)
        access_expires_at = now + timedelta(minutes=settings.jwt_access_token_minutes)
        refresh_expires_at = now + timedelta(days=settings.jwt_refresh_token_days)

        family = None
        if family_id is None:
            family = await self.token_families.create(AuthTokenFamily(user_id=user.id))
            family_id = family.id
        else:
            family = await self.token_families.get(family_id)
        if family is None:
            raise AppError(
                code="AUTH_SESSION_INVALID",
                message="Session token family tidak ditemukan.",
                status_code=401,
            )

        access_jti = str(uuid4())
        refresh_jti = str(uuid4())

        access_token = jwt.encode(
            self._build_claims(
                user=user,
                token_type="access",
                jti=access_jti,
                family_id=family_id,
                issued_at=now,
                expires_at=access_expires_at,
            ),
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        refresh_token = jwt.encode(
            self._build_claims(
                user=user,
                token_type="refresh",
                jti=refresh_jti,
                family_id=family_id,
                issued_at=now,
                expires_at=refresh_expires_at,
            ),
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        await self.refresh_tokens.create(
            AuthRefreshToken(
                family_id=family_id,
                user_id=user.id,
                jti=refresh_jti,
                token_hash=self._hash_token(refresh_token),
                expires_at=refresh_expires_at,
            )
        )
        return AuthTokenPairRead(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at,
        )

    async def _revoke_family(self, family: AuthTokenFamily, *, reason: str) -> None:
        now = datetime.now(UTC)
        if family.revoked_at is None:
            await self.token_families.update(
                family,
                revoked_at=now,
                revoked_reason=reason,
            )
        refresh_tokens = await self.refresh_tokens.list_by_family(family.id)
        for token in refresh_tokens:
            if token.revoked_at is None:
                await self.refresh_tokens.update(
                    token,
                    revoked_at=now,
                    revoked_reason=reason,
                )

    def _decode_token(self, token: str, *, expected_type: str) -> dict[str, object]:
        try:
            claims = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options={
                    "require": [
                        "sub",
                        "jti",
                        "type",
                        "iss",
                        "aud",
                        "iat",
                        "nbf",
                        "exp",
                        "sid",
                    ]
                },
            )
        except InvalidTokenError as exc:
            raise AppError(
                code="AUTH_TOKEN_INVALID",
                message="Token tidak valid atau sudah kedaluwarsa.",
                status_code=401,
            ) from exc
        if claims.get("type") != expected_type:
            raise AppError(
                code="AUTH_TOKEN_TYPE_INVALID",
                message="Jenis token tidak sesuai.",
                status_code=401,
            )
        return claims

    def _build_claims(
        self,
        *,
        user: AppUser,
        token_type: str,
        jti: str,
        family_id: UUID,
        issued_at: datetime,
        expires_at: datetime,
    ) -> dict[str, object]:
        claims: dict[str, object] = {
            "sub": str(user.id),
            "jti": jti,
            "sid": str(family_id),
            "type": token_type,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        if token_type == "access":
            claims["roles"] = user.roles
            claims["permissions"] = user.permissions
        return claims

    @staticmethod
    def hash_password(password: str) -> str:
        return password_hasher.hash(password)

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            return password_hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
