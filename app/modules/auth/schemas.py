from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class AuthRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class AuthTokenPairRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime


class AuthUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None


class AuthSessionRead(BaseModel):
    user: AuthUserRead
    tokens: AuthTokenPairRead
