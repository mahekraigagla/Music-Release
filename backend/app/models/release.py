"""
NextDrop – Release & Stream Models
------------------------------------
Release – Scheduling record linking a song to its actual release slot.
           Tracks expected vs. actual performance and locks model/dataset
           version metadata for full lineage.
Stream  – Weekly per-platform, per-country stream volume records used for
           post-release performance reporting and model retraining.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReleaseStatus


class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (
        CheckConstraint("release_day_of_week BETWEEN 1 AND 7", name="ck_release_dow"),
        CheckConstraint("release_hour BETWEEN 0 AND 23", name="ck_release_hour"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        unique=True,     # one release record per song
        nullable=False,
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ReleaseStatus.draft.value, index=True
    )
    scheduled_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    release_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    release_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI-predicted values at time of recommendation
    expected_streams: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expected_earnings: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Populated one week post-release by the data collection job
    actual_streams: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actual_earnings: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Version lineage – locks every release to the model + datasets used
    model_version: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("model_metadata.version"), nullable=True
    )
    dataset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    song: Mapped["Song"] = relationship("Song", back_populates="release")  # noqa: F821
    artist: Mapped["Artist"] = relationship("Artist", back_populates="releases")  # noqa: F821
    streams: Mapped[list["Stream"]] = relationship(
        "Stream", back_populates="release", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Release id={self.id} status={self.status!r} "
            f"day={self.release_day_of_week} hour={self.release_hour}>"
        )


class Stream(Base):
    """Weekly stream count partitioned by platform and country."""
    __tablename__ = "streams"
    __table_args__ = (
        CheckConstraint("week_number > 0", name="ck_stream_week"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    release_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("platforms.id"), nullable=False
    )
    country_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("countries.id"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stream_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    release: Mapped["Release"] = relationship("Release", back_populates="streams")
    platform: Mapped["Platform"] = relationship("Platform", back_populates="streams")  # noqa: F821
    country: Mapped["Country"] = relationship("Country", back_populates="streams")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Stream release_id={self.release_id} week={self.week_number} "
            f"count={self.stream_count}>"
        )
