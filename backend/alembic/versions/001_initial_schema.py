"""Initial schema – all tables

Revision ID: 001
Revises:
Create Date: 2026-07-19

Creates all tables in dependency order:
  1. Lookup tables (genres, moods, languages)
  2. Platforms, Countries
  3. Artists, ArtistStatistics, AudienceActivity
  4. Songs
  5. TimeSlots, MarketTrends
  6. ModelMetadata
  7. Releases, Streams
  8. FeatureStore, TrainingJobs
  9. ReleaseRecommendations, RecommendationCache, PredictionLogs
  10. AnalyticsSnapshots
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Lookup tables
    # ------------------------------------------------------------------
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_genres_name", "genres", ["name"])

    op.create_table(
        "moods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_moods_name", "moods", ["name"])

    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_languages_code", "languages", ["code"])

    # ------------------------------------------------------------------
    # 2. Platforms & Countries
    # ------------------------------------------------------------------
    op.create_table(
        "platforms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("payout_rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("growth_rate", sa.Numeric(5, 4), nullable=False, server_default="1.0000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_platforms_name", "platforms", ["name"])

    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cpm_multiplier", sa.Numeric(5, 4), nullable=False, server_default="1.0000"),
        sa.Column("market_growth_rate", sa.Numeric(5, 4), nullable=False, server_default="1.0000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_countries_code", "countries", ["code"])

    # ------------------------------------------------------------------
    # 3. Artists
    # ------------------------------------------------------------------
    op.create_table(
        "artists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("spotify_id", sa.String(100), nullable=True),
        sa.Column("youtube_id", sa.String(100), nullable=True),
        sa.Column("followers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_listeners", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("spotify_id"),
        sa.UniqueConstraint("youtube_id"),
    )
    op.create_index("ix_artists_name", "artists", ["name"])

    op.create_table(
        "artist_statistics",
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_releases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("previous_avg_streams", sa.Double(), nullable=False, server_default="0.0"),
        sa.Column("previous_avg_earnings", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("best_release_day", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("best_release_hour", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("follower_growth_rate", sa.Double(), nullable=False, server_default="0.0"),
        sa.Column("country_preference", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("platform_preference", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("engagement_rate", sa.Double(), nullable=False, server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("artist_id"),
    )

    op.create_table(
        "audience_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_matrix", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artist_id"),
    )

    # ------------------------------------------------------------------
    # 4. Songs
    # ------------------------------------------------------------------
    op.create_table(
        "songs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("isrc", sa.String(12), nullable=True),
        sa.Column("release_type", sa.String(20), nullable=False, server_default="single"),
        sa.Column("artwork_url", sa.String(512), nullable=True),
        sa.Column("audio_file_path", sa.String(512), nullable=True),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.Column("mood_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("danceability", sa.Numeric(4, 3), nullable=True),
        sa.Column("energy", sa.Numeric(4, 3), nullable=True),
        sa.Column("key", sa.Integer(), nullable=True),
        sa.Column("loudness", sa.Numeric(5, 2), nullable=True),
        sa.Column("mode", sa.Integer(), nullable=True),
        sa.Column("speechiness", sa.Numeric(4, 3), nullable=True),
        sa.Column("acousticness", sa.Numeric(4, 3), nullable=True),
        sa.Column("instrumentalness", sa.Numeric(4, 3), nullable=True),
        sa.Column("liveness", sa.Numeric(4, 3), nullable=True),
        sa.Column("valence", sa.Numeric(4, 3), nullable=True),
        sa.Column("tempo", sa.Numeric(5, 2), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("danceability BETWEEN 0 AND 1", name="ck_song_danceability"),
        sa.CheckConstraint("energy BETWEEN 0 AND 1", name="ck_song_energy"),
        sa.CheckConstraint("valence BETWEEN 0 AND 1", name="ck_song_valence"),
        sa.CheckConstraint("acousticness BETWEEN 0 AND 1", name="ck_song_acousticness"),
        sa.CheckConstraint("speechiness BETWEEN 0 AND 1", name="ck_song_speechiness"),
        sa.CheckConstraint("instrumentalness BETWEEN 0 AND 1", name="ck_song_instrumentalness"),
        sa.CheckConstraint("liveness BETWEEN 0 AND 1", name="ck_song_liveness"),
        sa.CheckConstraint("key BETWEEN -1 AND 11", name="ck_song_key"),
        sa.CheckConstraint("mode IN (0, 1)", name="ck_song_mode"),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.ForeignKeyConstraint(["mood_id"], ["moods.id"]),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isrc"),
    )
    op.create_index("ix_songs_artist_id", "songs", ["artist_id"])
    op.create_index("ix_songs_genre_id", "songs", ["genre_id"])

    # ------------------------------------------------------------------
    # 5. TimeSlots & MarketTrends
    # ------------------------------------------------------------------
    op.create_table(
        "time_slots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("release_hour", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("slot_name", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.CheckConstraint("day_of_week BETWEEN 1 AND 7", name="ck_ts_dow"),
        sa.CheckConstraint("release_hour BETWEEN 0 AND 23", name="ck_ts_hour"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("day_of_week", "release_hour", "timezone", name="uq_ts_slot"),
    )

    op.create_table(
        "market_trends",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trend_date", sa.Date(), nullable=False),
        sa.Column("time_slot_id", sa.Integer(), nullable=True),
        sa.Column("genre_id", sa.Integer(), nullable=True),
        sa.Column("stream_density_index", sa.Numeric(5, 4), nullable=False),
        sa.Column("growth_multiplier", sa.Numeric(5, 4), nullable=False, server_default="1.0000"),
        sa.Column("seasonality_index", sa.Numeric(5, 4), nullable=False, server_default="1.0000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["time_slot_id"], ["time_slots.id"]),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trend_date", "time_slot_id", "genre_id", name="uq_mt_entry"),
    )
    op.create_index("ix_market_trends_date", "market_trends", ["trend_date"])

    # ------------------------------------------------------------------
    # 6. Model Metadata (required before releases)
    # ------------------------------------------------------------------
    op.create_table(
        "model_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mae", sa.Double(), nullable=False),
        sa.Column("rmse", sa.Double(), nullable=False),
        sa.Column("r2", sa.Double(), nullable=False),
        sa.Column("hyperparameters", postgresql.JSONB(), nullable=False),
        sa.Column("features_list", postgresql.JSONB(), nullable=False),
        sa.Column("model_filepath", sa.String(255), nullable=False),
        sa.Column("dataset_version", sa.String(64), nullable=True),
        sa.Column("feature_version", sa.String(64), nullable=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
    )
    op.create_index("ix_model_metadata_version", "model_metadata", ["version"])

    # ------------------------------------------------------------------
    # 7. Releases & Streams
    # ------------------------------------------------------------------
    op.create_table(
        "releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("song_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_day_of_week", sa.Integer(), nullable=True),
        sa.Column("release_hour", sa.Integer(), nullable=True),
        sa.Column("expected_streams", sa.BigInteger(), nullable=True),
        sa.Column("expected_earnings", sa.Numeric(15, 2), nullable=True),
        sa.Column("actual_streams", sa.BigInteger(), nullable=True),
        sa.Column("actual_earnings", sa.Numeric(15, 2), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("dataset_version", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("release_day_of_week BETWEEN 1 AND 7", name="ck_release_dow"),
        sa.CheckConstraint("release_hour BETWEEN 0 AND 23", name="ck_release_hour"),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_version"], ["model_metadata.version"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("song_id"),
    )
    op.create_index("ix_releases_artist_id", "releases", ["artist_id"])
    op.create_index("ix_releases_status", "releases", ["status"])

    op.create_table(
        "streams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("stream_count", sa.BigInteger(), nullable=False),
        sa.Column("revenue", sa.Numeric(15, 4), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("week_number > 0", name="ck_stream_week"),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"]),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_streams_release_id", "streams", ["release_id"])

    # ------------------------------------------------------------------
    # 8. Feature Store & Training Jobs
    # ------------------------------------------------------------------
    op.create_table(
        "feature_store",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("song_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("features", postgresql.JSONB(), nullable=False),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("dataset_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_id"),
    )
    op.create_index("ix_feature_store_song_id", "feature_store", ["song_id"])

    op.create_table(
        "training_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("dataset_version", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("metrics_summary", postgresql.JSONB(), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_training_jobs_task_id", "training_jobs", ["task_id"])

    # ------------------------------------------------------------------
    # 9. Recommendations, Cache & Prediction Logs
    # ------------------------------------------------------------------
    op.create_table(
        "release_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("song_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_goal", sa.String(50), nullable=False),
        sa.Column("input_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("selected_time_slot_id", sa.Integer(), nullable=True),
        sa.Column("recommended_time_slot_id", sa.Integer(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_time_slot_id"], ["time_slots.id"]),
        sa.ForeignKeyConstraint(["recommended_time_slot_id"], ["time_slots.id"]),
        sa.ForeignKeyConstraint(["model_version"], ["model_metadata.version"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_release_recommendations_song_id", "release_recommendations", ["song_id"])
    op.create_index("ix_release_recommendations_artist_id", "release_recommendations", ["artist_id"])

    op.create_table(
        "recommendation_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("song_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommended_slot_id", sa.Integer(), nullable=True),
        sa.Column("recommendations_payload", postgresql.JSONB(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recommended_slot_id"], ["time_slots.id"]),
        sa.ForeignKeyConstraint(["model_version"], ["model_metadata.version"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("song_id"),
    )

    op.create_table(
        "prediction_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("predictions", postgresql.JSONB(), nullable=False),
        sa.Column("shap_values", postgresql.JSONB(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["release_recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_version"], ["model_metadata.version"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recommendation_id"),
    )

    # ------------------------------------------------------------------
    # 10. Analytics Snapshots
    # ------------------------------------------------------------------
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("followers_count", sa.Integer(), nullable=False),
        sa.Column("monthly_listeners_count", sa.Integer(), nullable=False),
        sa.Column("weekly_streams_count", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artist_id", "snapshot_date", name="uq_snapshot"),
    )
    op.create_index("ix_analytics_snapshots_artist_id", "analytics_snapshots", ["artist_id"])


def downgrade() -> None:
    # Drop in reverse order
    op.drop_table("analytics_snapshots")
    op.drop_table("prediction_logs")
    op.drop_table("recommendation_cache")
    op.drop_table("release_recommendations")
    op.drop_table("training_jobs")
    op.drop_table("feature_store")
    op.drop_table("streams")
    op.drop_table("releases")
    op.drop_table("model_metadata")
    op.drop_table("market_trends")
    op.drop_table("time_slots")
    op.drop_table("songs")
    op.drop_table("audience_activity")
    op.drop_table("artist_statistics")
    op.drop_table("artists")
    op.drop_table("countries")
    op.drop_table("platforms")
    op.drop_table("languages")
    op.drop_table("moods")
    op.drop_table("genres")
