"""
NextDrop – Recommendation Engine & Dynamic RSS Scoring
-------------------------------------------------------
Computes predictions across 35 time slots (7 days × 5 hours) and ranks them using
the 4-part Release Strategy Score:

    RSS(d,h) = w1 * S_hat(d,h) + w2 * C(d,h) + w3 * M_n(d,h) + w4 * G(d,h)

Combines XGBoost ML predictions with dynamic artist scale, genre velocity, and artist goals.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.ml.explainability.explainer import ModelExplainer
from app.models.enums import ArtistGoal


class RecommendationEngine:
    """Core Release Strategy Recommendation Engine."""

    GENRE_SLOT_WEIGHTS = {
        "pop": {5: 1.35, 4: 1.20, 6: 1.10},       # Friday peak, Thursday early
        "hip-hop": {4: 1.35, 5: 1.30, 3: 1.10},   # Thursday night drop, Friday
        "electronic": {5: 1.30, 6: 1.35, 7: 1.15},# Friday/Saturday weekend party
        "rock": {3: 1.25, 4: 1.30, 5: 1.15},      # Mid-week & Thursday
        "r&b": {4: 1.25, 5: 1.30, 7: 1.20},       # Thursday/Sunday late
        "indie": {2: 1.20, 3: 1.25, 4: 1.30},     # Tuesday-Thursday indie drops
    }

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path or settings.active_model_path
        self._load_active_artifact()

    def _load_active_artifact(self) -> None:
        """Load active model artifact from disk."""
        path = Path(self.model_path)
        if not path.exists():
            logger.warning(f"Active model artifact not found at {path}. Model evaluation will use heuristic fallback.")
            self.artifact = None
            self.model = None
            self.pipeline = None
            self.explainer = None
            return

        try:
            self.artifact = joblib.load(path)
            self.model = self.artifact["model"]
            self.pipeline = self.artifact["pipeline"]
            feature_names = self.artifact.get("feature_names", [])
            self.explainer = ModelExplainer(self.model, feature_names)
            logger.info(f"Loaded active model version: {self.artifact.get('version', 'unknown')}")
        except Exception as e:
            logger.error(f"Error loading model artifact ({e}).")
            self.artifact = None
            self.model = None
            self.pipeline = None
            self.explainer = None

    def calculate_rss(
        self,
        predicted_streams: float,
        confidence_index: float,
        market_opportunity_score: float,
        goal_alignment_score: float,
        artist_listeners: int = 10000,
        weights: tuple[float, float, float, float] = (0.45, 0.20, 0.20, 0.15),
    ) -> float:
        """
        Compute 4-part Release Strategy Score (0 to 100 scale).
        """
        w1, w2, w3, w4 = weights
        # Dynamic normalization relative to artist listener baseline
        target_scale = max(5000.0, float(artist_listeners * 1.5))
        s_norm = min(1.0, max(0.05, predicted_streams / target_scale))

        rss = 100.0 * (
            w1 * s_norm
            + w2 * confidence_index
            + w3 * market_opportunity_score
            + w4 * goal_alignment_score
        )
        return round(float(rss), 2)

    def recommend(
        self,
        song_metadata: dict[str, Any],
        artist_statistics: dict[str, Any],
        artist_goal: str = ArtistGoal.maximum_streams.value,
        time_slots: list[dict[str, Any]] | None = None,
        top_n: int = 5,
    ) -> dict[str, Any]:
        """
        Generate ranked top-N release slot recommendations across 35 time slots.
        """
        if time_slots is None or len(time_slots) == 0:
            day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
            hours = {10: "Morning", 14: "Afternoon", 16: "Late Afternoon", 18: "Evening", 21: "Night"}
            time_slots = [
                {"id": (d - 1) * 5 + i + 1, "day_of_week": d, "release_hour": h, "slot_name": f"{day_names[d]} {label}"}
                for d in range(1, 8)
                for i, (h, label) in enumerate(hours.items())
            ]

        # Extract artist monthly listeners & derive historical stats
        m_listeners = int(artist_statistics.get("monthly_listeners", 25000))
        prev_releases = int(artist_statistics.get("previous_releases", 3))
        prev_streams = float(artist_statistics.get("previous_avg_streams", max(1000.0, m_listeners * 0.75)))

        # Normalize genre to lowercase
        genre_clean = str(song_metadata.get("genre", "pop")).lower().strip()
        song_clean = {**song_metadata, "genre": genre_clean, "language": str(song_metadata.get("language", "en")).lower()}

        artist_stats_clean = {
            "previous_releases": prev_releases,
            "previous_avg_streams": prev_streams,
            "follower_growth_rate": 0.03,
            "engagement_rate": 0.06,
        }

        # Prepare base feature vector
        base_record = {**song_clean, **artist_stats_clean}
        eval_records = []

        for slot in time_slots:
            rec = {**base_record}
            rec["release_day_of_week"] = slot["day_of_week"]
            rec["release_hour"] = slot["release_hour"]
            eval_records.append(rec)

        df_eval = pd.DataFrame(eval_records)

        # 1. ML Model Prediction across all 35 slots
        if self.model is not None and self.pipeline is not None:
            X_eval = self.pipeline.transform(df_eval)
            log_preds = self.model.predict(X_eval)
            raw_model_streams = np.expm1(log_preds)
            attributions_sample = self.explainer.explain_prediction(X_eval[0]) if self.explainer else []
        else:
            raw_model_streams = np.array([prev_streams * 1.2] * len(time_slots))
            attributions_sample = []

        # 2. Dynamic Slot & Genre Sensitivity Adjustment
        genre_weights = self.GENRE_SLOT_WEIGHTS.get(genre_clean, {5: 1.3, 4: 1.15})
        predicted_streams = []

        for idx, slot in enumerate(time_slots):
            dow = slot["day_of_week"]
            hour = slot["release_hour"]

            # Genre multiplier for this day
            g_mult = genre_weights.get(dow, 0.95)

            # Hour velocity multiplier
            if hour in (16, 18):
                h_mult = 1.25  # Prime afternoon/evening
            elif hour == 21:
                h_mult = 1.15  # Night drop
            else:
                h_mult = 0.90  # Morning/early afternoon

            # Dynamic predicted stream calculation (scaled by artist listener capacity)
            base_model_pred = float(raw_model_streams[idx])
            stream_potential = (0.4 * base_model_pred + 0.6 * (prev_streams * 1.2)) * g_mult * h_mult
            predicted_streams.append(max(100.0, float(stream_potential)))

        # 3. Compute RSS for each slot
        slot_scores = []
        for idx, slot in enumerate(time_slots):
            pred_s = float(predicted_streams[idx])
            dow = slot["day_of_week"]
            hour = slot["release_hour"]

            # Confidence factor
            conf = 0.92 if dow in (4, 5) else (0.82 if dow == 6 else 0.70)

            # Market Opportunity Score (varies dynamically by hour and genre)
            market_opp = 0.88 if (dow in (4, 5) and hour in (16, 18)) else 0.65

            # Goal Alignment multiplier
            if artist_goal == ArtistGoal.maximum_streams.value:
                goal_align = 1.0 if dow == 5 else (0.85 if dow == 4 else 0.65)
            elif artist_goal == ArtistGoal.maximum_revenue.value:
                goal_align = 1.0 if dow in (4, 5) else 0.75
            elif artist_goal == ArtistGoal.audience_growth.value:
                goal_align = 1.0 if dow in (2, 3, 4) else 0.70  # Mid-week growth
            else:  # Playlist Reach
                goal_align = 1.0 if dow == 4 else (0.90 if dow == 5 else 0.60)  # Thursday pre-pitching

            rss = self.calculate_rss(pred_s, conf, market_opp, goal_align, artist_listeners=m_listeners)
            payout_inr = 0.28 if artist_goal == ArtistGoal.maximum_revenue.value else 0.22
            exp_earnings_inr = round(pred_s * payout_inr, 2)

            slot_scores.append({
                "time_slot_id": slot.get("id"),
                "day_of_week": dow,
                "release_hour": hour,
                "slot_name": slot["slot_name"],
                "predicted_streams": int(round(pred_s)),
                "expected_earnings_inr": exp_earnings_inr,
                "expected_earnings_usd": round(exp_earnings_inr / 83.5, 2),
                "confidence_index": round(conf, 2),
                "market_opportunity_score": round(market_opp, 2),
                "goal_alignment_score": round(goal_align, 2),
                "release_strategy_score": rss,
            })

        # 4. Sort by RSS descending and pick top-N
        slot_scores.sort(key=lambda x: x["release_strategy_score"], reverse=True)
        top_recommendations = slot_scores[:top_n]

        return {
            "model_version": self.artifact.get("version", "v1.0-fallback") if self.artifact else "v1.0-heuristic",
            "artist_goal": artist_goal,
            "top_recommendations": top_recommendations,
            "all_slot_scores": slot_scores,
            "feature_attributions": attributions_sample,
        }
