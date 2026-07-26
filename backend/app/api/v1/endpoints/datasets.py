"""
NextDrop – Datasets API Endpoint
---------------------------------
GET /api/v1/datasets
POST /api/v1/ingest-datasets
Manages raw/merged dataset file listings and triggers the row-level ingestion pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from app.core.config import settings
from app.ml.datasets.loader import compute_file_sha256
from app.ml.datasets.preprocessor import DatasetPreprocessor

router = APIRouter(tags=["MLOps"])


@router.get("/datasets", summary="List raw & merged dataset inventory")
async def list_datasets() -> dict:
    raw_files = []
    if settings.data_raw_dir.exists():
        for p in settings.data_raw_dir.iterdir():
            if p.is_file() and not p.name.startswith("."):
                raw_files.append({
                    "filename": p.name,
                    "size_bytes": p.stat().st_size,
                    "sha256": compute_file_sha256(p)[:16] + "...",
                })

    merged_info = None
    merged_path = settings.data_merged_dir / "merged_dataset.parquet"
    if merged_path.exists():
        merged_info = {
            "filename": merged_path.name,
            "size_bytes": merged_path.stat().st_size,
            "sha256": compute_file_sha256(merged_path)[:16] + "...",
        }

    return {
        "raw_datasets": raw_files,
        "merged_dataset": merged_info,
    }


@router.post("/ingest-datasets", summary="Run dataset ingestion & validation pipeline")
async def run_ingestion() -> dict:
    try:
        df, summary = DatasetPreprocessor().run_pipeline()
        return {
            "status": "success",
            "message": "Dataset ingestion and merging complete.",
            "merged_records": len(df),
            "summary": summary,
        }
    except Exception as e:
        logger.error(f"Ingestion error ({e})")
        raise HTTPException(status_code=500, detail=str(e))
