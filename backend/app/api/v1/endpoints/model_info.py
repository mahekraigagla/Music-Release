"""NextDrop – Model Info Endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.ml import ModelMetadata

router = APIRouter(tags=["System"])


@router.get("/model-info", summary="Active model metadata")
async def model_info(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Returns metadata of the currently active model version.
    Returns 503 if the database is unreachable.
    Returns 404 if no model has been trained yet.
    Does not require authentication – useful for monitoring dashboards.
    """
    try:
        result = await db.execute(
            select(ModelMetadata).where(ModelMetadata.is_active == True).limit(1)
        )
        model = result.scalar_one_or_none()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "DATABASE_UNAVAILABLE",
                "message": "Cannot reach the database. Ensure PostgreSQL is running and DATABASE_URL is correct.",
            },
        )

    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "NO_ACTIVE_MODEL",
                "message": "No active model found. Run POST /api/v1/train-model to train the first model.",
            },
        )

    return {
        "model_version": model.version,
        "is_active": model.is_active,
        "dataset_version": model.dataset_version,
        "feature_version": model.feature_version,
        "metrics": {
            "mae": model.mae,
            "rmse": model.rmse,
            "r2": model.r2,
        },
        "hyperparameters": model.hyperparameters,
        "model_filepath": model.model_filepath,
        "trained_at": model.trained_at.isoformat(),
    }

