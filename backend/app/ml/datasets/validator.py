"""
NextDrop – Dataset Validator Module
------------------------------------
Performs row-level data validation adhering strictly to production rules:
  1. No synthetic target extrapolation for non-charting songs.
  2. Invalid/out-of-bounds rows are DISCARDED (never silently clamped).
  3. Every validation action is audited and logged.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from loguru import logger


class DatasetValidator:
    """Row-level validator for track, chart, and feature dataframes."""

    AUDIO_FEATURE_BOUNDS = {
        "danceability": (0.0, 1.0),
        "energy": (0.0, 1.0),
        "valence": (0.0, 1.0),
        "acousticness": (0.0, 1.0),
        "speechiness": (0.0, 1.0),
        "instrumentalness": (0.0, 1.0),
        "liveness": (0.0, 1.0),
        "loudness": (-60.0, 5.0),
        "tempo": (40.0, 250.0),
        "key": (-1, 11),
        "mode": (0, 1),
        "duration_ms": (30000, 1800000),
    }

    def __init__(self) -> None:
        self.audit_log: list[dict[str, Any]] = []

    def log_validation(self, check_name: str, rows_before: int, rows_after: int, reason: str) -> None:
        dropped = rows_before - rows_after
        entry = {
            "check": check_name,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_dropped": dropped,
            "reason": reason,
        }
        self.audit_log.append(entry)
        if dropped > 0:
            logger.warning(
                f"[Validation] {check_name}: Dropped {dropped:,} invalid rows ({reason}). "
                f"Remaining: {rows_after:,}"
            )
        else:
            logger.info(f"[Validation] {check_name}: All {rows_after:,} rows passed.")

    def validate_tracks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate track metadata and audio features."""
        initial_len = len(df)
        df_clean = df.copy()

        # 1. Deduplicate by track/song title + artist
        title_col = "track_name" if "track_name" in df_clean.columns else "title"
        artist_col = "artists" if "artists" in df_clean.columns else "artist_name"

        if title_col in df_clean.columns and artist_col in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=[title_col, artist_col])
            self.log_validation(
                "Track Deduplication", initial_len, len(df_clean), f"Duplicate {title_col}+{artist_col}"
            )

        # 2. Check required columns non-null
        curr_len = len(df_clean)
        required_cols = [c for c in [title_col, artist_col] if c in df_clean.columns]
        if required_cols:
            df_clean = df_clean.dropna(subset=required_cols)
            self.log_validation("Required Columns Null Check", curr_len, len(df_clean), "Null in required track/artist name")

        # 3. Audio feature boundary validation (discard invalid rows, NO clamping)
        for col, (min_val, max_val) in self.AUDIO_FEATURE_BOUNDS.items():
            if col in df_clean.columns:
                curr = len(df_clean)
                valid_mask = df_clean[col].isna() | (
                    (df_clean[col] >= min_val) & (df_clean[col] <= max_val)
                )
                df_clean = df_clean[valid_mask]
                self.log_validation(
                    f"Boundary Check: {col}",
                    curr,
                    len(df_clean),
                    f"{col} out of bounds [{min_val}, {max_val}]",
                )

        return df_clean

    def validate_charts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate chart data and stream targets."""
        initial_len = len(df)
        df_clean = df.copy()

        # 1. Non-negative streams
        stream_col = "streams" if "streams" in df_clean.columns else "stream_count"
        if stream_col in df_clean.columns:
            df_clean = df_clean.dropna(subset=[stream_col])
            df_clean = df_clean[df_clean[stream_col] > 0]
            self.log_validation(
                "Positive Streams Check",
                initial_len,
                len(df_clean),
                "Missing or non-positive stream counts",
            )

        return df_clean

    def get_audit_summary(self) -> dict[str, Any]:
        """Return structured summary of all validation actions."""
        total_dropped = sum(e["rows_dropped"] for e in self.audit_log)
        return {
            "total_checks": len(self.audit_log),
            "total_rows_dropped": total_dropped,
            "audit_log": self.audit_log,
        }
