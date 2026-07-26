"""
NextDrop – Application Settings
--------------------------------
All configuration is loaded from environment variables (or a .env file).
Pydantic-Settings handles validation, type coercion, and defaults.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = "NextDrop AI Release Strategist"
    app_env: str = Field("development", pattern="^(development|staging|production)$")
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # -------------------------------------------------------------------------
    # Security / JWT
    # -------------------------------------------------------------------------
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str  # asyncpg URL
    database_sync_url: str  # psycopg2 URL (Alembic + Celery)
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # -------------------------------------------------------------------------
    # Redis / Celery
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # -------------------------------------------------------------------------
    # File Storage Paths
    # -------------------------------------------------------------------------
    data_raw_dir: Path = Path("data/raw")
    data_processed_dir: Path = Path("data/processed")
    data_merged_dir: Path = Path("data/merged")
    data_features_dir: Path = Path("data/features")
    data_models_dir: Path = Path("data/models")
    audio_upload_dir: Path = Path("uploads/audio")
    max_audio_upload_size_mb: int = 50

    # -------------------------------------------------------------------------
    # ML Configuration
    # -------------------------------------------------------------------------
    active_model_path: Path = Path("data/models/release_model.pkl")
    optuna_n_trials: int = 100
    optuna_timeout_seconds: int = 3600
    cv_n_splits: int = 5
    early_stopping_rounds: int = 20
    top_n_recommendations: int = 5

    # -------------------------------------------------------------------------
    # Feature Drift Thresholds
    # -------------------------------------------------------------------------
    psi_warning_threshold: float = 0.1
    psi_alert_threshold: float = 0.25

    # -------------------------------------------------------------------------
    # External APIs
    # -------------------------------------------------------------------------
    mapbox_access_token: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    allowed_origins: str = "http://localhost:3000"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        # Stored as comma-separated string; the property below converts to list.
        return v

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # -------------------------------------------------------------------------
    # Derived helpers
    # -------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def ensure_directories(self) -> None:
        """Create all required data/upload directories if they don't exist."""
        for path in [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_merged_dir,
            self.data_features_dir,
            self.data_models_dir,
            self.audio_upload_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (evaluated once at startup)."""
    return Settings()


# Module-level convenience alias used throughout the app.
settings = get_settings()
