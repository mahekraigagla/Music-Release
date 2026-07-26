"""
NextDrop – Release History Endpoint
------------------------------------
GET /api/v1/release-history
Returns artist release recommendations and actual post-release performance logs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.release import Release

router = APIRouter(tags=["Strategy"])


@router.get("/release-history", summary="Fetch past release strategy history")
async def get_release_history(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        result = await db.execute(select(Release).limit(50))
        releases = result.scalars().all()
        history = [
            {
                "id": str(r.id),
                "song_id": str(r.song_id),
                "status": r.status,
                "scheduled_time": r.scheduled_time.isoformat() if r.scheduled_time else None,
                "release_day_of_week": r.release_day_of_week,
                "release_hour": r.release_hour,
                "expected_streams": r.expected_streams,
                "actual_streams": r.actual_streams,
                "model_version": r.model_version,
            }
            for r in releases
        ]
    except Exception:
        history = []

    return {
        "count": len(history),
        "history": history,
    }
