"""
NextDrop – Model Training CLI Script
-------------------------------------
Loads merged training data, runs Optuna + XGBoost training, and registers the active
model version in PostgreSQL:
    python -m scripts.train_pipeline
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.database import sync_engine
from app.core.config import settings
from app.models.ml import ModelMetadata
from app.ml.training.trainer import ModelTrainer


def register_model_metadata(summary: dict) -> None:
    """Save model version metadata to PostgreSQL ModelMetadata table."""
    with Session(sync_engine) as session:
        # Deactivate all previous models
        session.execute(update(ModelMetadata).values(is_active=False))

        # Insert new active model
        meta = ModelMetadata(
            version=summary["model_version"],
            is_active=True,
            mae=summary["metrics"]["mae"],
            rmse=summary["metrics"]["rmse"],
            r2=summary["metrics"]["r2"],
            hyperparameters=summary["best_params"],
            features_list=[],
            model_filepath=summary["model_filepath"],
            dataset_version=summary["dataset_version"],
            feature_version=summary["feature_version"],
        )
        session.add(meta)
        session.commit()
        print(f"Registered model {summary['model_version']} in PostgreSQL database as active model.")


def main():
    print("=" * 60)
    print("NextDrop AI Release Strategist – ML Training Pipeline")
    print("=" * 60)

    merged_path = settings.data_merged_dir / "merged_dataset.parquet"
    if not merged_path.exists():
        print(f"Merged dataset missing at {merged_path}. Running ingestion first...")
        from app.ml.datasets.preprocessor import DatasetPreprocessor
        preprocessor = DatasetPreprocessor()
        df, _ = preprocessor.run_pipeline()
    else:
        print(f"Loading merged dataset from {merged_path}...")
        df = pd.read_parquet(merged_path)

    trainer = ModelTrainer()
    summary = trainer.train_model(df, n_trials=10)

    # Register in DB
    try:
        register_model_metadata(summary)
    except Exception as e:
        print(f"Warning: Could not register model in DB ({e}). Model file saved locally.")

    print("\n" + "=" * 60)
    print("Training Results:")
    print("-" * 60)
    print(f"Model Version: {summary['model_version']}")
    print(f"Dataset Version: {summary['dataset_version']}")
    print(f"MAE:  {summary['metrics']['mae']:,.2f} streams")
    print(f"RMSE: {summary['metrics']['rmse']:,.2f}")
    print(f"R²:   {summary['metrics']['r2']:.4f}")
    print(f"Model File: {summary['model_filepath']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
