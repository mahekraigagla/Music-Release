"""
NextDrop – Model Training Endpoint
-----------------------------------
POST /api/v1/train-model
Triggers model re-training using Optuna + XGBoost on the latest merged dataset.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
import pandas as pd

from app.core.config import settings
from app.ml.training.trainer import ModelTrainer
from scripts.train_pipeline import register_model_metadata

router = APIRouter(tags=["MLOps"])


def run_training_task():
    merged_path = settings.data_merged_dir / "merged_dataset.parquet"
    if not merged_path.exists():
        from app.ml.datasets.preprocessor import DatasetPreprocessor
        df, _ = DatasetPreprocessor().run_pipeline()
    else:
        df = pd.read_parquet(merged_path)

    trainer = ModelTrainer()
    summary = trainer.train_model(df, n_trials=10)
    register_model_metadata(summary)


@router.post("/train-model", summary="Trigger ML Model Retraining")
async def trigger_training(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(run_training_task)
    return {
        "status": "accepted",
        "message": "Model retraining task initiated in background.",
    }
