from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.types import TimestampMixin, UUIDPrimaryKeyMixin


class AppUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "app_users"

    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    token_families: Mapped[list[AuthTokenFamily]] = relationship(back_populates="user")


class AuthTokenFamily(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auth_token_families"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)

    user: Mapped[AppUser] = relationship(back_populates="token_families")
    refresh_tokens: Mapped[list[AuthRefreshToken]] = relationship(back_populates="family")


class AuthRefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auth_refresh_tokens"
    __table_args__ = (
        UniqueConstraint("jti", name="uq_auth_refresh_tokens_jti"),
        UniqueConstraint("token_hash", name="uq_auth_refresh_tokens_token_hash"),
    )

    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_token_families.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(String(36), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)
    replaced_by_jti: Mapped[str | None] = mapped_column(String(36))

    family: Mapped[AuthTokenFamily] = relationship(back_populates="refresh_tokens")
    user: Mapped[AppUser] = relationship()
