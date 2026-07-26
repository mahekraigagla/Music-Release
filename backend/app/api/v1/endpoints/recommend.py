"""
NextDrop – Recommendation Endpoint
------------------------------------
POST /api/v1/recommend
Calculates predictions across all 35 time slots and returns ranked top-N strategies.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.ml.feature_engineering.audio import AudioFeatureExtractor
from app.ml.recommendation.engine import RecommendationEngine
from app.ml.recommendation.explainer import StrategyExplainer
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.core.config import settings

router = APIRouter(tags=["Strategy"])

engine = RecommendationEngine()
explainer = StrategyExplainer()
audio_extractor = AudioFeatureExtractor()


@router.post("/analyze-audio", summary="Extract audio features from uploaded MP3/WAV file")
async def analyze_audio_file(file: UploadFile = File(...)) -> dict:
    """
    Upload an MP3/WAV song file to analyze acoustic features (tempo, energy, danceability, valence, key, loudness).
    """
    import tempfile
    upload_dir = settings.audio_upload_dir
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        upload_dir = Path(tempfile.gettempdir()) / "audio_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix or ".mp3"
    temp_filename = f"upload_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = upload_dir / temp_filename

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        features = audio_extractor.extract_features(file_path)
        features["file_name"] = file.filename
        features["file_path"] = str(file_path)
        return {
            "status": "success",
            "filename": file.filename,
            "features": features,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio file: {str(e)}",
        )


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Generate Release Strategy Recommendation",
)
async def generate_recommendation(
    payload: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Computes predictions across all 35 time slots (7 days x 5 hours),
    calculates the 4-part Release Strategy Score (RSS), and returns the optimal drop window.
    """
    song_dict = payload.song.model_dump()

    # Extract audio features if path provided
    if payload.audio_file_path:
        try:
            audio_feats = audio_extractor.extract_features(payload.audio_file_path)
            song_dict.update(audio_feats)
        except Exception as err:
            logger.warning(f"Could not extract features from {payload.audio_file_path}: {err}")

    artist_stats = {
        "followers": payload.followers,
        "monthly_listeners": payload.monthly_listeners,
        "previous_releases": payload.previous_releases,
        "previous_avg_streams": max(1000.0, float(payload.monthly_listeners / max(1, payload.previous_releases))),
        "follower_growth_rate": 0.03,
        "engagement_rate": 0.06,
    }

    # Generate recommendations
    res = engine.recommend(
        song_metadata=song_dict,
        artist_statistics=artist_stats,
        artist_goal=payload.artist_goal.value,
        top_n=5,
    )

    top_recs = res["top_recommendations"]
    primary_slot = top_recs[0]

    # Generate strategy explanation report
    report = explainer.generate_strategy_report(
        song_title=payload.song.title,
        artist_name=payload.song.artist_name,
        top_rec=primary_slot,
        attributions=res.get("feature_attributions", []),
        genre=payload.song.genre,
        goal=payload.artist_goal.value,
    )

    return {
        "model_version": res["model_version"],
        "artist_goal": payload.artist_goal.value,
        "primary_recommendation": primary_slot,
        "top_5_recommendations": top_recs,
        "headline": report["headline"],
        "summary": report["summary"],
        "key_drivers": report["key_drivers"],
        "tactical_checklist": report["tactical_checklist"],
        "feature_attributions": report.get("translated_attributions", res.get("feature_attributions", [])),
    }
