"""
NextDrop – Artist, ArtistStatistics & AudienceActivity Models
--------------------------------------------------------------
Artist           – Core profile record.
ArtistStatistics – Pre-aggregated personalization features, updated after
                   each release. This is the primary source of artist-history
                   features fed into the XGBoost model.
AudienceActivity – 7×24 listening density matrix derived from Last.fm data.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Double, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    spotify_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    youtube_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    followers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_listeners: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    statistics: Mapped["ArtistStatistics | None"] = relationship(
        "ArtistStatistics", back_populates="artist", uselist=False, cascade="all, delete-orphan"
    )
    audience_activity: Mapped["AudienceActivity | None"] = relationship(
        "AudienceActivity", back_populates="artist", uselist=False, cascade="all, delete-orphan"
    )
    songs: Mapped[list["Song"]] = relationship("Song", back_populates="artist")  # noqa: F821
    releases: Mapped[list["Release"]] = relationship("Release", back_populates="artist")  # noqa: F821
    analytics_snapshots: Mapped[list["AnalyticsSnapshot"]] = relationship(  # noqa: F821
        "AnalyticsSnapshot", back_populates="artist"
    )

    def __repr__(self) -> str:
        return f"<Artist id={self.id} name={self.name!r}>"


class ArtistStatistics(Base):
    """
    Aggregated personalization features for the XGBoost model.
    Updated via the `update_artist_statistics` service call after each release
    reaches its 7-day mark and actual streams are recorded.

    Represents X_hist in the ML pipeline feature vector.
    """
    __tablename__ = "artist_statistics"

    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artists.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # X_hist components
    previous_releases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previous_avg_streams: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    previous_avg_earnings: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, default=0.00
    )
    # 1 = Monday … 7 = Sunday; defaults to Friday (5) as global mode
    best_release_day: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    # 0–23; defaults to 18 (6 PM) as global mode
    best_release_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    # Weekly percentage follower change (e.g. 0.05 = 5% growth)
    follower_growth_rate: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    # e.g. {"US": 0.60, "GB": 0.20, "IN": 0.10}
    country_preference: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # e.g. {"spotify": 0.70, "apple_music": 0.20, "youtube": 0.10}
    platform_preference: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Interaction rate (saves + shares / streams)
    engagement_rate: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    artist: Mapped["Artist"] = relationship("Artist", back_populates="statistics")

    def __repr__(self) -> str:
        return (
            f"<ArtistStatistics artist_id={self.artist_id} "
            f"previous_releases={self.previous_releases}>"
        )


class AudienceActivity(Base):
    """
    7×24 listening density matrix (7 days × 24 hours = 168 cells).
    Derived from Last.fm timestamps via the offline aggregation pipeline.

    activity_matrix layout:
        activity_matrix[day_index][hour] where day_index 0=Monday … 6=Sunday
        and each value is the normalized probability of a listen event A(d,h).
    """
    __tablename__ = "audience_activity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artists.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    # Stored as [[0.01, 0.02, ...], [...], ...] – 7 rows × 24 columns
    activity_matrix: Mapped[list] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    artist: Mapped["Artist"] = relationship("Artist", back_populates="audience_activity")

    def __repr__(self) -> str:
        return f"<AudienceActivity artist_id={self.artist_id}>"
