"""
NextDrop – Model Trainer Module
--------------------------------
Trains a global XGBRegressor model with Optuna hyperparameter optimization,
cross-validation, and early stopping.
Stores artifacts to disk and updates ModelMetadata in PostgreSQL.
"""

from __future__ import annotations

import joblib
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import pandas as pd
from loguru import logger
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from app.core.config import settings
from app.ml.feature_engineering.pipeline import FeaturePipeline


# Quiet Optuna logs during execution
optuna.logging.set_verbosity(optuna.logging.WARNING)


class ModelTrainer:
    """XGBoost + Optuna model trainer."""

    def __init__(self, model_dir: Path | None = None) -> None:
        self.model_dir = model_dir or settings.data_models_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def train_model(
        self,
        df: pd.DataFrame,
        target_col: str = "target_streams",
        dataset_version: str = "v1.0",
        feature_version: str = "v1.0",
        n_trials: int = 20,
    ) -> dict[str, Any]:
        """
        Train XGBRegressor using Optuna hyperparameter optimization.
        Target is trained on log1p(streams) for scale stability.
        """
        logger.info(f"Starting model training on {len(df):,} records...")

        # 1. Feature Engineering
        pipeline = FeaturePipeline()
        X, feature_names = pipeline.fit_transform(df)
        y = np.log1p(df[target_col].values.astype(np.float64))

        # Train/Test Split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 2. Optuna Objective
        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 9),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
                "random_state": 42,
                "n_jobs": -1,
            }

            model = XGBRegressor(**params, early_stopping_rounds=15)
            model.fit(
                X_train,
                y_train,
                eval_set=[(X_test, y_test)],
                verbose=False,
            )

            preds = model.predict(X_test)
            return float(mean_squared_error(y_test, preds))

        logger.info(f"Running Optuna study with {n_trials} trials...")
        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials)

        best_params = study.best_params
        logger.info(f"Optuna complete. Best params: {best_params}")

        # 3. Final Model Training with Best Parameters
        final_model = XGBRegressor(**best_params, early_stopping_rounds=20, random_state=42)
        final_model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        # 4. Evaluation Metrics (converted back from log scale)
        log_preds = final_model.predict(X_test)
        y_test_orig = np.expm1(y_test)
        y_pred_orig = np.expm1(log_preds)

        mae = float(mean_absolute_error(y_test_orig, y_pred_orig))
        rmse = float(np.sqrt(mean_squared_error(y_test_orig, y_pred_orig)))
        r2 = float(r2_score(y_test, log_preds))  # R2 in log space

        logger.info(f"Model Evaluation -> MAE: {mae:,.2f} streams | RMSE: {rmse:,.2f} | R2: {r2:.4f}")

        # 5. Persist Artifacts
        model_version = f"v{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        model_filename = f"release_model_{model_version}.pkl"
        model_path = self.model_dir / model_filename
        active_path = settings.active_model_path

        artifact = {
            "model": final_model,
            "pipeline": pipeline,
            "feature_names": feature_names,
            "best_params": best_params,
            "version": model_version,
            "dataset_version": dataset_version,
            "feature_version": feature_version,
            "metrics": {"mae": mae, "rmse": rmse, "r2": r2},
        }

        joblib.dump(artifact, model_path)
        joblib.dump(artifact, active_path)  # Overwrite active model symlink/file

        logger.info(f"Model artifact saved to {model_path} and active path {active_path}")

        return {
            "model_version": model_version,
            "dataset_version": dataset_version,
            "feature_version": feature_version,
            "metrics": {"mae": mae, "rmse": rmse, "r2": r2},
            "best_params": best_params,
            "model_filepath": str(model_path),
            "feature_count": len(feature_names),
        }
