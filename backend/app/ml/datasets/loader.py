"""
NextDrop – Dataset Loader Module
----------------------------------
Handles loading datasets in CSV, TSV, or Parquet format and computes cryptographic
SHA-256 version hashes for dataset lineage tracking.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

import pandas as pd
from loguru import logger

from app.core.config import settings


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file for dataset versioning."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_dataframe_sha256(df: pd.DataFrame) -> str:
    """Compute SHA-256 hash of a pandas DataFrame's underlying values."""
    data_bytes = pd.util.hash_pandas_object(df, index=True).values.tobytes()
    return hashlib.sha256(data_bytes).hexdigest()


class DatasetLoader:
    """Loader utility for raw and processed music datasets."""

    def __init__(self, raw_dir: Path | None = None) -> None:
        self.raw_dir = raw_dir or settings.data_raw_dir

    def load_dataset(
        self,
        filename: str,
        file_format: Literal["csv", "tsv", "parquet"] | None = None,
        **kwargs,
    ) -> tuple[pd.DataFrame, str]:
        """
        Load a dataset file from raw directory.

        Returns:
            Tuple of (DataFrame, SHA-256 file hash).
        """
        candidates = [
            self.raw_dir / filename,
            Path("..") / self.raw_dir / filename,
            self.raw_dir / (filename + ".csv"),
            Path("..") / self.raw_dir / (filename + ".csv"),
            self.raw_dir / (filename + ".tsv"),
            Path("..") / self.raw_dir / (filename + ".tsv"),
        ]
        filepath = None
        for cand in candidates:
            if cand.exists():
                filepath = cand
                break

        if filepath is None:
            raise FileNotFoundError(
                f"Dataset file not found: {filename} in {self.raw_dir.absolute()} or parent data/raw."
            )

        if file_format is None:
            if filename.endswith(".csv"):
                file_format = "csv"
            elif filename.endswith(".tsv"):
                file_format = "tsv"
            elif filename.endswith(".parquet") or filename.endswith(".pq"):
                file_format = "parquet"
            else:
                file_format = "csv"

        logger.info(f"Loading dataset: {filename} (Format: {file_format})")
        file_hash = compute_file_sha256(filepath)

        if file_format == "csv":
            df = pd.read_csv(filepath, **kwargs)
        elif file_format == "tsv":
            df = pd.read_csv(filepath, sep="\t", **kwargs)
        elif file_format == "parquet":
            df = pd.read_parquet(filepath, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        logger.info(f"Loaded {len(df):,} rows from {filename} [SHA-256: {file_hash[:12]}...]")
        return df, file_hash
