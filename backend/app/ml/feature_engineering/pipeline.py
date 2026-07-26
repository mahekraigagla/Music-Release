"""
NextDrop – Feature Engineering Pipeline
----------------------------------------
Builds the unified 4-part feature vector:
    X = X_audio ⊕ X_hist ⊕ X_market ⊕ X_temporal

Strictly re-used across offline training and online inference to prevent train-serving skew.
OneHotEncoder is applied ONLY to low-cardinality categorical features (genre, language).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from loguru import logger


class FeaturePipeline:
    """Feature engineering pipeline for offline training and online recommendation."""

    NUMERICAL_AUDIO_FEATURES = [
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "duration_ms",
    ]

    NUMERICAL_HISTORICAL_FEATURES = [
        "previous_releases",
        "previous_avg_streams",
        "follower_growth_rate",
        "engagement_rate",
    ]

    NUMERICAL_INTERACTION_FEATURES = [
        "rhythmic_potency",
        "emotional_intensity",
        "acoustic_energy_ratio",
        "listener_velocity",
    ]

    NUMERICAL_MARKET_FEATURES = [
        "stream_density_index",
        "growth_multiplier",
        "seasonality_index",
    ]

    NUMERICAL_TEMPORAL_FEATURES = [
        "day_of_week",
        "release_hour",
        "is_weekend",
        "is_peak_hour",
    ]

    CATEGORICAL_FEATURES = ["genre", "language"]

    def __init__(self) -> None:
        self.encoder: OneHotEncoder | None = None
        self.feature_names: list[str] = []
        self.is_fitted: bool = False

    def _extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derive temporal features from release day and hour columns."""
        df_temp = pd.DataFrame(index=df.index)

        if "release_day_of_week" in df.columns:
            dow = pd.Series(df["release_day_of_week"], index=df.index)
        elif "day_of_week" in df.columns:
            dow = pd.Series(df["day_of_week"], index=df.index)
        else:
            dow = pd.Series(5, index=df.index)

        if "release_hour" in df.columns:
            hour = pd.Series(df["release_hour"], index=df.index)
        else:
            hour = pd.Series(18, index=df.index)

        df_temp["day_of_week"] = dow
        df_temp["release_hour"] = hour
        df_temp["is_weekend"] = ((dow == 6) | (dow == 7)).astype(int)
        df_temp["is_peak_hour"] = ((hour >= 16) & (hour <= 21)).astype(int)
        return df_temp

    def prepare_raw_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fills missing feature columns with intelligent domain defaults."""
        df_proc = df.copy()

        # Fill audio defaults
        audio_defaults = {
            "danceability": 0.60,
            "energy": 0.65,
            "key": 5,
            "loudness": -7.0,
            "mode": 1,
            "speechiness": 0.05,
            "acousticness": 0.20,
            "instrumentalness": 0.05,
            "liveness": 0.15,
            "valence": 0.55,
            "tempo": 120.0,
            "duration_ms": 210000,
        }
        for col, default_val in audio_defaults.items():
            if col not in df_proc.columns:
                df_proc[col] = default_val
            else:
                df_proc[col] = df_proc[col].fillna(default_val)

        # Fill historical defaults
        hist_defaults = {
            "previous_releases": 1,
            "previous_avg_streams": 10000.0,
            "follower_growth_rate": 0.02,
            "engagement_rate": 0.05,
        }
        for col, default_val in hist_defaults.items():
            if col not in df_proc.columns:
                df_proc[col] = default_val
            else:
                df_proc[col] = df_proc[col].fillna(default_val)

        # Fill market defaults
        market_defaults = {
            "stream_density_index": 0.50,
            "growth_multiplier": 1.0,
            "seasonality_index": 1.0,
        }
        for col, default_val in market_defaults.items():
            if col not in df_proc.columns:
                df_proc[col] = default_val
            else:
                df_proc[col] = df_proc[col].fillna(default_val)

        # Fill categorical defaults
        if "genre" not in df_proc.columns:
            df_proc["genre"] = "Pop"
        else:
            df_proc["genre"] = df_proc["genre"].fillna("Pop")

        if "language" not in df_proc.columns:
            df_proc["language"] = "en"
        else:
            df_proc["language"] = df_proc["language"].fillna("en")

        # Derive interaction features
        df_proc["rhythmic_potency"] = df_proc["danceability"] * df_proc["tempo"]
        df_proc["emotional_intensity"] = df_proc["energy"] * df_proc["valence"]
        df_proc["acoustic_energy_ratio"] = df_proc["energy"] / (df_proc["acousticness"] + 1e-4)
        df_proc["listener_velocity"] = df_proc["previous_avg_streams"] / (df_proc["previous_releases"] + 1.0)

        return df_proc

    def fit_transform(self, df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        """Fit OneHotEncoder and transform training feature dataframe."""
        df_proc = self.prepare_raw_features(df)
        df_temp = self._extract_temporal_features(df_proc)

        num_cols = (
            self.NUMERICAL_AUDIO_FEATURES
            + self.NUMERICAL_HISTORICAL_FEATURES
            + self.NUMERICAL_INTERACTION_FEATURES
            + self.NUMERICAL_MARKET_FEATURES
        )
        X_num = df_proc[num_cols].values
        X_temp = df_temp[self.NUMERICAL_TEMPORAL_FEATURES].values

        # OneHotEncode low-cardinality categoricals ONLY
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        X_cat = self.encoder.fit_transform(df_proc[self.CATEGORICAL_FEATURES])

        cat_feature_names = list(self.encoder.get_feature_names_out(self.CATEGORICAL_FEATURES))
        self.feature_names = num_cols + self.NUMERICAL_TEMPORAL_FEATURES + cat_feature_names

        X_full = np.hstack([X_num, X_temp, X_cat])
        self.is_fitted = True
        logger.info(f"Fitted FeaturePipeline: {X_full.shape[1]} total features created.")
        return X_full, self.feature_names

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform inference data using the fitted encoder."""
        if not self.is_fitted or self.encoder is None:
            raise RuntimeError("FeaturePipeline must be fitted before calling transform().")

        df_proc = self.prepare_raw_features(df)
        df_temp = self._extract_temporal_features(df_proc)

        num_cols = (
            self.NUMERICAL_AUDIO_FEATURES
            + self.NUMERICAL_HISTORICAL_FEATURES
            + self.NUMERICAL_INTERACTION_FEATURES
            + self.NUMERICAL_MARKET_FEATURES
        )
        X_num = df_proc[num_cols].values
        X_temp = df_temp[self.NUMERICAL_TEMPORAL_FEATURES].values
        X_cat = self.encoder.transform(df_proc[self.CATEGORICAL_FEATURES])

        return np.hstack([X_num, X_temp, X_cat])
