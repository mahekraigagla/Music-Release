"""
NextDrop – Recommendation API Schemas
---------------------------------------
Pydantic schemas for recommendation request and response models.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.models.enums import ArtistGoal, ReleaseType


class SongMetadataInput(BaseModel):
    title: str = Field(..., example="Midnight Pulse")
    artist_name: str = Field(..., example="Neon Wave")
    release_type: ReleaseType = Field(default=ReleaseType.single)
    genre: str = Field(default="Pop")
    mood: str = Field(default="Energetic")
    language: str = Field(default="en")

    # Optional acoustic features (if already extracted)
    danceability: Optional[float] = Field(default=0.65, ge=0.0, le=1.0)
    energy: Optional[float] = Field(default=0.70, ge=0.0, le=1.0)
    valence: Optional[float] = Field(default=0.60, ge=0.0, le=1.0)
    tempo: Optional[float] = Field(default=120.0, ge=40.0, le=250.0)


class RecommendationRequest(BaseModel):
    song: SongMetadataInput
    artist_goal: ArtistGoal = Field(default=ArtistGoal.maximum_streams)
    followers: int = Field(default=15000, ge=0)
    monthly_listeners: int = Field(default=45000, ge=0)
    previous_releases: int = Field(default=3, ge=0)
    audio_file_path: Optional[str] = Field(default=None)


class RecommendedSlotSchema(BaseModel):
    time_slot_id: Optional[int]
    day_of_week: int
    release_hour: int
    slot_name: str
    predicted_streams: int
    expected_earnings_usd: float
    confidence_index: float
    market_opportunity_score: float
    goal_alignment_score: float
    release_strategy_score: float


class RecommendationResponse(BaseModel):
    model_version: str
    artist_goal: str
    primary_recommendation: RecommendedSlotSchema
    top_5_recommendations: List[RecommendedSlotSchema]
    headline: str
    summary: str
    key_drivers: List[str]
    tactical_checklist: List[str]
    feature_attributions: List[dict]
