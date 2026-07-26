"""NextDrop – Health Check Endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(tags=["System"])


@router.get("/health", summary="Server health check")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Returns service health status.
    Checks:
      - Application is running.
      - Database is reachable.
    """
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_env": settings.app_env,
        "database_connected": db_ok,
        "active_model_path": str(settings.active_model_path),
        "active_model_loaded": settings.active_model_path.exists(),
    }
