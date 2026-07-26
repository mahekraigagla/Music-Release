"""NextDrop – API v1 Router."""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.model_info import router as model_info_router

from app.api.v1.endpoints.recommend import router as recommend_router
from app.api.v1.endpoints.predict import router as predict_router
from app.api.v1.endpoints.train import router as train_router
from app.api.v1.endpoints.datasets import router as datasets_router
from app.api.v1.endpoints.history import router as history_router

api_router = APIRouter()

# System endpoints
api_router.include_router(health_router)
api_router.include_router(model_info_router)

# Core Feature endpoints
api_router.include_router(recommend_router)
api_router.include_router(predict_router)
api_router.include_router(train_router)
api_router.include_router(datasets_router)
api_router.include_router(history_router)
