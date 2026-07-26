"""
NextDrop – Song Model
----------------------
Stores track-level metadata and Spotify audio features.
Audio features (danceability, energy, etc.) may be NULL when the song is
first uploaded and are populated after Librosa extraction completes.
ISRC is optional – the fallback is title+artist matching.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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
from app.models.enums import ReleaseType


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = (
        CheckConstraint("danceability BETWEEN 0 AND 1", name="ck_song_danceability"),
        CheckConstraint("energy BETWEEN 0 AND 1", name="ck_song_energy"),
        CheckConstraint("valence BETWEEN 0 AND 1", name="ck_song_valence"),
        CheckConstraint("acousticness BETWEEN 0 AND 1", name="ck_song_acousticness"),
        CheckConstraint("speechiness BETWEEN 0 AND 1", name="ck_song_speechiness"),
        CheckConstraint("instrumentalness BETWEEN 0 AND 1", name="ck_song_instrumentalness"),
        CheckConstraint("liveness BETWEEN 0 AND 1", name="ck_song_liveness"),
        CheckConstraint("key BETWEEN -1 AND 11", name="ck_song_key"),
        CheckConstraint("mode IN (0, 1)", name="ck_song_mode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Catalog metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    isrc: Mapped[str | None] = mapped_column(String(12), unique=True, nullable=True)
    release_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ReleaseType.single.value
    )
    artwork_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    audio_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Normalized lookup FKs
    genre_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("genres.id"), nullable=False, index=True
    )
    mood_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("moods.id"), nullable=False, index=True
    )
    language_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("languages.id"), nullable=False, index=True
    )

    # Spotify / Librosa audio features (nullable until extraction is complete)
    danceability: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    energy: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    key: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loudness: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    mode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speechiness: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    acousticness: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    instrumentalness: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    liveness: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    valence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    tempo: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    artist: Mapped["Artist"] = relationship("Artist", back_populates="songs")  # noqa: F821
    genre: Mapped["Genre"] = relationship("Genre", back_populates="songs")  # noqa: F821
    mood: Mapped["Mood"] = relationship("Mood", back_populates="songs")  # noqa: F821
    language: Mapped["Language"] = relationship("Language", back_populates="songs")  # noqa: F821
    release: Mapped["Release | None"] = relationship(  # noqa: F821
        "Release", back_populates="song", uselist=False, cascade="all, delete-orphan"
    )
    feature_store_entry: Mapped["FeatureStore | None"] = relationship(  # noqa: F821
        "FeatureStore", back_populates="song", uselist=False
    )
    recommendations: Mapped[list["ReleaseRecommendation"]] = relationship(  # noqa: F821
        "ReleaseRecommendation", back_populates="song"
    )
    recommendation_cache: Mapped["RecommendationCache | None"] = relationship(  # noqa: F821
        "RecommendationCache", back_populates="song", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Song id={self.id} title={self.title!r} artist_id={self.artist_id}>"
