"""
NextDrop – Single Prediction Endpoint
--------------------------------------
POST /api/v1/predict
Predicts 7-day streams and earnings for a single specific time slot.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ml.recommendation.engine import RecommendationEngine
from app.schemas.recommendation import SongMetadataInput

router = APIRouter(tags=["Strategy"])
engine = RecommendationEngine()


class SinglePredictionRequest(BaseModel):
    song: SongMetadataInput
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday ... 7=Sunday")
    release_hour: int = Field(..., ge=0, le=23, description="0 to 23 hour in UTC")
    monthly_listeners: int = Field(default=25000, ge=0)


@router.post("/predict", summary="Predict streams for a specific release slot")
async def predict_single_slot(payload: SinglePredictionRequest) -> dict:
    song_dict = payload.song.model_dump()
    artist_stats = {
        "monthly_listeners": payload.monthly_listeners,
        "previous_releases": 3,
        "previous_avg_streams": payload.monthly_listeners * 0.8,
    }

    res = engine.recommend(
        song_metadata=song_dict,
        artist_statistics=artist_stats,
        top_n=35,
    )

    # Find the requested slot
    matched = None
    for slot in res["all_slot_scores"]:
        if slot["day_of_week"] == payload.day_of_week and slot["release_hour"] == payload.release_hour:
            matched = slot
            break

    if not matched:
        matched = res["top_recommendations"][0]

    return {
        "model_version": res["model_version"],
        "day_of_week": payload.day_of_week,
        "release_hour": payload.release_hour,
        "slot_name": matched["slot_name"],
        "predicted_streams": matched["predicted_streams"],
        "expected_earnings_usd": matched["expected_earnings_usd"],
        "release_strategy_score": matched["release_strategy_score"],
    }
