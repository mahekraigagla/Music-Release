"""
NextDrop – Platform & Country Models
--------------------------------------
Platform stores per-stream payout rates configurable via the admin API.
Country stores market performance multipliers by ISO-3166 alpha-2 code.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    # Per-stream payout in USD (e.g. 0.003500 for Spotify)
    payout_rate: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    # Rolling platform growth multiplier (1.0 = no growth, 1.15 = 15% growth)
    growth_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    streams: Mapped[list["Stream"]] = relationship("Stream", back_populates="platform")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Platform name={self.name!r} payout_rate={self.payout_rate}>"


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ISO-3166-1 alpha-2, e.g. "US", "GB", "IN"
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # CPM multiplier relative to global average (1.0 = average, 1.5 = 50% above)
    cpm_multiplier: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    market_growth_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    streams: Mapped[list["Stream"]] = relationship("Stream", back_populates="country")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Country code={self.code!r} name={self.name!r}>"
