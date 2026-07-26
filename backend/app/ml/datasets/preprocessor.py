"""
NextDrop – Dataset Preprocessor & Merger
------------------------------------------
Preprocesses raw Spotify tracks, Spotify charts, and Last.fm activity data:
  - Standardises track title and artist names for robust fallback matching.
  - Aggregates Last.fm listening timestamps into 7×24 weekly listening matrices.
  - Joins tracks + charts + artist activity to form the unified training dataset.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.ml.datasets.loader import DatasetLoader
from app.ml.datasets.validator import DatasetValidator


def normalize_string(val: str | None) -> str:
    """Normalize string for string-matching join fallback."""
    if not isinstance(val, str) or pd.isna(val):
        return ""
    val = val.lower().strip()
    val = re.sub(r"[^\w\s]", "", val)
    return re.sub(r"\s+", " ", val)


class DatasetPreprocessor:
    """Preprocessor for merging raw music datasets into a unified dataset."""

    def __init__(self, raw_dir: Path | None = None) -> None:
        self.loader = DatasetLoader(raw_dir)
        self.validator = DatasetValidator()

    def process_lastfm_activity(self, df_lastfm: pd.DataFrame) -> dict[str, np.ndarray]:
        """
        Process Last.fm activity records to compute a 7x24 listening matrix per artist.

        Matrix layout: shape (7, 24) where row 0 = Monday ... row 6 = Sunday,
        and each cell holds the normalized probability of listen events.
        """
        logger.info("Processing Last.fm timestamps into 7x24 audience activity matrices...")
        # Expected columns: user_id, timestamp, artist_name, track_name
        artist_col = [c for c in ["artist_name", "artist", "artists"] if c in df_lastfm.columns]
        time_col = [c for c in ["timestamp", "time", "date"] if c in df_lastfm.columns]

        if not artist_col or not time_col:
            logger.warning("Last.fm dataset missing required artist or timestamp columns.")
            return {}

        a_col = artist_col[0]
        t_col = time_col[0]

        df_lfm = df_lastfm.dropna(subset=[a_col, t_col]).copy()
        df_lfm["dt"] = pd.to_datetime(df_lfm[t_col], errors="coerce")
        df_lfm = df_lfm.dropna(subset=["dt"])

        df_lfm["day_of_week"] = df_lfm["dt"].dt.dayofweek  # 0=Monday … 6=Sunday
        df_lfm["hour"] = df_lfm["dt"].dt.hour
        df_lfm["norm_artist"] = df_lfm[a_col].apply(normalize_string)

        matrices: dict[str, np.ndarray] = {}
        grouped = df_lfm.groupby(["norm_artist", "day_of_week", "hour"]).size()

        for norm_artist, sub in grouped.groupby(level=0):
            matrix = np.zeros((7, 24), dtype=np.float64)
            for (_, dow, hr), count in sub.items():
                matrix[dow, hr] = count

            total_events = matrix.sum()
            if total_events > 0:
                matrix /= total_events  # Normalize to sum = 1.0

            matrices[norm_artist] = matrix

        logger.info(f"Generated 7x24 audience matrices for {len(matrices):,} artists.")
        return matrices

    def run_pipeline(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Run complete dataset ingestion, cleaning, and merging pipeline."""
        logger.info("Starting dataset preprocessing pipeline...")
        audit_summary = {}

        # 1. Load Spotify tracks
        tracks_df, tracks_hash = self.loader.load_dataset("spotify_tracks.csv")
        tracks_df = self.validator.validate_tracks(tracks_df)

        # Standardise names for fallback join
        title_col = "track_name" if "track_name" in tracks_df.columns else "title"
        artist_col = "artists" if "artists" in tracks_df.columns else "artist_name"

        tracks_df["norm_title"] = tracks_df[title_col].apply(normalize_string)
        tracks_df["norm_artist"] = tracks_df[artist_col].apply(normalize_string)

        # 2. Load Spotify charts
        try:
            charts_df, charts_hash = self.loader.load_dataset("spotify_charts.csv", nrows=500000, on_bad_lines="skip")
            charts_df = self.validator.validate_charts(charts_df)

            c_title = "track_name" if "track_name" in charts_df.columns else "title"
            c_artist = "artist" if "artist" in charts_df.columns else "artist_name"
            stream_col = "streams" if "streams" in charts_df.columns else "stream_count"

            charts_df["norm_title"] = charts_df[c_title].apply(normalize_string)
            charts_df["norm_artist"] = charts_df[c_artist].apply(normalize_string)

            # Aggregate target stream potential per track
            chart_summary = (
                charts_df.groupby(["norm_title", "norm_artist"])[stream_col]
                .agg(["max", "mean", "count"])
                .reset_index()
                .rename(columns={"max": "target_streams", "mean": "avg_streams", "count": "chart_weeks"})
            )
        except Exception as e:
            logger.warning(f"Could not process spotify_charts.csv ({e}). Using synthetic target fallback for testing.")
            chart_summary = pd.DataFrame(columns=["norm_title", "norm_artist", "target_streams", "avg_streams", "chart_weeks"])
            charts_hash = "N/A"

        # 3. Load Last.fm activity
        try:
            lastfm_df, lastfm_hash = self.loader.load_dataset("lastfm_activity.tsv", nrows=500000, on_bad_lines="skip")
            audience_matrices = self.process_lastfm_activity(lastfm_df)
        except Exception as e:
            logger.warning(f"Could not process lastfm_activity.tsv ({e}).")
            audience_matrices = {}
            lastfm_hash = "N/A"

        # 4. Merge tracks with chart targets
        if not chart_summary.empty:
            merged_df = pd.merge(
                tracks_df,
                chart_summary,
                on=["norm_title", "norm_artist"],
                how="inner",  # Train only on records with reliable observed targets
            )
            logger.info(f"Merged tracks with chart targets: {len(merged_df):,} matched songs.")
        else:
            merged_df = tracks_df.copy()
            # Fallback for baseline dataset testing
            if "popularity" in merged_df.columns:
                merged_df["target_streams"] = (merged_df["popularity"] ** 2.5 * 100).astype(int)
            else:
                merged_df["target_streams"] = 50000

        # Save merged dataset
        settings.data_merged_dir.mkdir(parents=True, exist_ok=True)
        output_path = settings.data_merged_dir / "merged_dataset.parquet"
        merged_df.to_parquet(output_path, index=False)

        audit_summary = self.validator.get_audit_summary()
        audit_summary["dataset_hashes"] = {
            "spotify_tracks": tracks_hash,
            "spotify_charts": charts_hash,
            "lastfm_activity": lastfm_hash,
        }
        audit_summary["merged_rows"] = len(merged_df)
        audit_summary["output_filepath"] = str(output_path)

        logger.info(f"Merged dataset saved to {output_path} ({len(merged_df):,} rows).")
        return merged_df, audit_summary
