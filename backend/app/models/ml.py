"""
NextDrop – ML & Audit Models
------------------------------
ModelMetadata       – Tracks every trained model version, its metrics, and
                      the hyperparameters used. Only one row has is_active=True.
TrainingJob         – Audits Celery training task executions.
FeatureStore        – Persists compiled feature vectors per song for audit
                      and retraining. Locked to dataset + feature versions.
ReleaseRecommendation – Business-level recommendation history; one row per
                      strategy session (not overwritten on re-runs).
RecommendationCache – Active dashboard cache; one row per song, evicted when
                      the song's release record changes.
PredictionLog       – Low-level ML output store: raw 35-slot predictions +
                      SHAP arrays. Referenced from ReleaseRecommendation.
AnalyticsSnapshot   – Periodic artist performance snapshots for drift monitoring.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ArtistGoal, TrainingJobStatus


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Semantic version tag used as FK in releases and caches
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mae: Mapped[float] = mapped_column(Double, nullable=False)
    rmse: Mapped[float] = mapped_column(Double, nullable=False)
    r2: Mapped[float] = mapped_column(Double, nullable=False)
    hyperparameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    features_list: Mapped[list] = mapped_column(JSONB, nullable=False)
    model_filepath: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feature_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ModelMetadata version={self.version!r} active={self.is_active}>"


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TrainingJobStatus.pending.value
    )
    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    metrics_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<TrainingJob task_id={self.task_id!r} status={self.status!r}>"


class FeatureStore(Base):
    __tablename__ = "feature_store"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("releases.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Full serialized feature dict (key=feature_name, value=processed value)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    feature_version: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    song: Mapped["Song"] = relationship("Song", back_populates="feature_store_entry")  # noqa: F821

    def __repr__(self) -> str:
        return f"<FeatureStore song_id={self.song_id} feature_version={self.feature_version!r}>"


class ReleaseRecommendation(Base):
    """Immutable business audit of each strategy generation run."""
    __tablename__ = "release_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artist_goal: Mapped[str] = mapped_column(String(50), nullable=False)
    input_parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Time slot chosen by the artist (may differ from recommended)
    selected_time_slot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("time_slots.id"), nullable=True
    )
    # Top system recommendation
    recommended_time_slot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("time_slots.id"), nullable=True
    )
    model_version: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("model_metadata.version"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    song: Mapped["Song"] = relationship("Song", back_populates="recommendations")  # noqa: F821
    prediction_log: Mapped["PredictionLog | None"] = relationship(
        "PredictionLog", back_populates="recommendation", uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ReleaseRecommendation id={self.id} goal={self.artist_goal!r}>"


class RecommendationCache(Base):
    """Active dashboard cache – one row per song, updated on each run."""
    __tablename__ = "recommendation_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    recommended_slot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("time_slots.id"), nullable=True
    )
    # Full serialised API response payload (top-5 slots, explanation, timeline)
    recommendations_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("model_metadata.version"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    song: Mapped["Song"] = relationship("Song", back_populates="recommendation_cache")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RecommendationCache song_id={self.song_id}>"


class PredictionLog(Base):
    """Low-level ML outputs store – raw 35-slot predictions + SHAP arrays."""
    __tablename__ = "prediction_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("release_recommendations.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )
    # Full array: [{"slot": {...}, "predicted_streams": float}, ...]
    predictions: Mapped[list] = mapped_column(JSONB, nullable=False)
    # Local SHAP values per recommended slot: {"feature": shap_value, ...}
    shap_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("model_metadata.version"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    recommendation: Mapped["ReleaseRecommendation | None"] = relationship(
        "ReleaseRecommendation", back_populates="prediction_log"
    )

    def __repr__(self) -> str:
        return f"<PredictionLog recommendation_id={self.recommendation_id}>"


class AnalyticsSnapshot(Base):
    """Periodic artist metrics snapshot used for PSI drift monitoring."""
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        UniqueConstraint("artist_id", "snapshot_date", name="uq_snapshot"),
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
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    followers_count: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_listeners_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weekly_streams_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    artist: Mapped["Artist"] = relationship("Artist", back_populates="analytics_snapshots")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot artist_id={self.artist_id} date={self.snapshot_date}>"
