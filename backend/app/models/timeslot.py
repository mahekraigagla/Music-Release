"""
NextDrop – TimeSlot & MarketTrend Models
------------------------------------------
TimeSlot    – Administrator-configured release hour/day combinations.
              The recommendation engine reads available slots from this table
              at runtime, so adding or removing slots never requires a code
              deployment.
MarketTrend – Stores public market trend indicators derived from Spotify
              Charts data (genre velocity, seasonality, platform growth).
              Replaces the competition_calendar concept — we model
              market opportunity, not competitor schedules.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimeSlot(Base):
    __tablename__ = "time_slots"
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 1 AND 7", name="ck_ts_dow"),
        CheckConstraint("release_hour BETWEEN 0 AND 23", name="ck_ts_hour"),
        UniqueConstraint("day_of_week", "release_hour", "timezone", name="uq_ts_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 1 = Monday … 7 = Sunday
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    release_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    # IANA timezone string (e.g. 'UTC', 'America/New_York')
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    slot_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    market_trends: Mapped[list["MarketTrend"]] = relationship(
        "MarketTrend", back_populates="time_slot"
    )

    def __repr__(self) -> str:
        return (
            f"<TimeSlot id={self.id} dow={self.day_of_week} "
            f"hour={self.release_hour} tz={self.timezone!r}>"
        )


class MarketTrend(Base):
    """
    Public trend indicators for a given date × time_slot × genre combination.
    Populated by the offline ingestion pipeline using Spotify Charts data.

    Components feed into the Market Opportunity Score M_n(t):
        stream_density_index  → ChartVelocity(t)
        growth_multiplier     → PlatformGrowth(p)
        seasonality_index     → Seasonality(t)
    """
    __tablename__ = "market_trends"
    __table_args__ = (
        UniqueConstraint("trend_date", "time_slot_id", "genre_id", name="uq_mt_entry"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trend_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time_slot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("time_slots.id"), nullable=True, index=True
    )
    genre_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("genres.id"), nullable=True, index=True
    )
    # Normalized stream density index (0–1 scale across all slots for that date)
    stream_density_index: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    # Rolling growth multiplier (1.0 = baseline)
    growth_multiplier: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    # Seasonal index for this date relative to annual baseline
    seasonality_index: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    time_slot: Mapped["TimeSlot | None"] = relationship(
        "TimeSlot", back_populates="market_trends"
    )
    genre: Mapped["Genre | None"] = relationship("Genre", back_populates="market_trends")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<MarketTrend date={self.trend_date} slot_id={self.time_slot_id} "
            f"genre_id={self.genre_id}>"
        )
