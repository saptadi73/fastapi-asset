from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.types import TimestampMixin, UUIDPrimaryKeyMixin


class AssetScanEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_scan_events"
    __table_args__ = (UniqueConstraint("event_uid", name="uq_asset_scan_events_event_uid"),)

    event_uid: Mapped[UUID]
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=True,
    )
    asset_tag_id: Mapped[UUID | None] = mapped_column(nullable=True)
    raw_tag_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    scan_type: Mapped[str] = mapped_column(String(30), nullable=False)
    scan_source: Mapped[str] = mapped_column(String(30), nullable=False)
    device_id: Mapped[UUID | None] = mapped_column(nullable=True)
    scanned_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    gps_accuracy_meters: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scanned_by: Mapped[UUID | None] = mapped_column(nullable=True)
    transfer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_transfers.id", ondelete="RESTRICT"),
        nullable=True,
    )
    stocktake_session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_stocktake_sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    match_status: Mapped[str] = mapped_column(String(30), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)

    asset = relationship("Asset")
    scanned_location = relationship("AssetLocation")
    transfer = relationship("AssetTransfer")
    stocktake_session = relationship("AssetStocktakeSession", back_populates="scan_events")
    verifications: Mapped[list[AssetVerification]] = relationship(
        back_populates="scan_event"
    )
    stocktake_results: Mapped[list[AssetStocktakeResult]] = relationship(
        back_populates="scan_event"
    )


class AssetVerification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_verifications"

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scan_event_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_scan_events.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    observed_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    verification_result: Mapped[str] = mapped_column(String(30), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_by: Mapped[UUID | None] = mapped_column(nullable=True)
    expected_custodian_id: Mapped[UUID | None] = mapped_column(nullable=True)
    observed_custodian_id: Mapped[UUID | None] = mapped_column(nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    resolved_by: Mapped[UUID | None] = mapped_column(nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_action: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)

    asset = relationship("Asset")
    scan_event: Mapped[AssetScanEvent] = relationship(back_populates="verifications")
    expected_location = relationship("AssetLocation", foreign_keys=[expected_location_id])
    observed_location = relationship("AssetLocation", foreign_keys=[observed_location_id])


class AssetStocktakeSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_stocktake_sessions"

    session_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    planned_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    location = relationship("AssetLocation")
    expected_items: Mapped[list[AssetStocktakeExpectedItem]] = relationship(
        back_populates="stocktake_session"
    )
    results: Mapped[list[AssetStocktakeResult]] = relationship(back_populates="stocktake_session")
    scan_events: Mapped[list[AssetScanEvent]] = relationship(back_populates="stocktake_session")


class AssetStocktakeExpectedItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "asset_stocktake_expected_items"
    __table_args__ = (
        UniqueConstraint(
            "stocktake_session_id",
            "asset_id",
            name="uq_stocktake_expected_session_asset",
        ),
    )

    stocktake_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_stocktake_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_location_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_custodian_id: Mapped[UUID | None] = mapped_column(nullable=True)
    snapshot_status: Mapped[str] = mapped_column(String(30), nullable=False)

    stocktake_session: Mapped[AssetStocktakeSession] = relationship(back_populates="expected_items")
    asset = relationship("Asset")
    expected_location = relationship("AssetLocation")


class AssetStocktakeResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_stocktake_results"
    __table_args__ = (
        UniqueConstraint(
            "stocktake_session_id",
            "asset_id",
            "result_type",
            name="uq_stocktake_result_session_asset_type",
        ),
    )

    stocktake_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("asset_stocktake_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=True,
    )
    scan_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_scan_events.id", ondelete="RESTRICT"),
        nullable=True,
    )
    result_type: Mapped[str] = mapped_column(String(30), nullable=False)
    observed_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("asset_locations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    resolution_reference_type: Mapped[str | None] = mapped_column(String(30))
    resolution_reference_id: Mapped[UUID | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)

    stocktake_session: Mapped[AssetStocktakeSession] = relationship(back_populates="results")
    asset = relationship("Asset")
    scan_event: Mapped[AssetScanEvent | None] = relationship(back_populates="stocktake_results")
    observed_location = relationship("AssetLocation")
