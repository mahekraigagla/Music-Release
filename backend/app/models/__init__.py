"""
NextDrop – Models Package
--------------------------
Imports all ORM models so that:
  1. Alembic's `env.py` can discover them by importing this module.
  2. Relationship back-references resolve without circular import issues.
"""

from app.models.lookups import Genre, Language, Mood
from app.models.platform import Country, Platform
from app.models.artist import Artist, ArtistStatistics, AudienceActivity
from app.models.song import Song
from app.models.release import Release, Stream
from app.models.timeslot import MarketTrend, TimeSlot
from app.models.ml import (
    AnalyticsSnapshot,
    FeatureStore,
    ModelMetadata,
    PredictionLog,
    RecommendationCache,
    ReleaseRecommendation,
    TrainingJob,
)

__all__ = [
    # Lookups
    "Genre",
    "Mood",
    "Language",
    # Platform
    "Platform",
    "Country",
    # Artist
    "Artist",
    "ArtistStatistics",
    "AudienceActivity",
    # Song
    "Song",
    # Release
    "Release",
    "Stream",
    # Scheduling
    "TimeSlot",
    "MarketTrend",
    # ML / Audit
    "ModelMetadata",
    "TrainingJob",
    "FeatureStore",
    "ReleaseRecommendation",
    "RecommendationCache",
    "PredictionLog",
    "AnalyticsSnapshot",
]
