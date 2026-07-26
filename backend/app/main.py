"""
NextDrop – FastAPI Application Entrypoint
------------------------------------------
Configures the FastAPI application with:
  - CORS middleware
  - Global RFC-7807-style exception handlers
  - Startup / shutdown database lifecycle events
  - API v1 router mounted at /api/v1
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: verify DB, create directories. Shutdown: dispose engine."""
    logger.info(f"Starting {settings.app_name} [{settings.app_env}]")
    settings.ensure_directories()
    try:
        await init_db()
        logger.info("Database connection verified.")
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        logger.warning("Application starting up in degraded mode (no database connection).")
    yield
    await close_db()
    logger.info("Database connection closed.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI-powered music release strategy platform. "
            "Predicts chart-level streaming potential across 35 time slots "
            "and recommends optimal release strategies."
        ),
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------------
    # Global exception handlers (RFC-7807 format)
    # -------------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled exception on {request.method} {request.url}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "details": [],
            },
        )

    # -------------------------------------------------------------------------
    # Routers & Dashboard
    # -------------------------------------------------------------------------
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    from fastapi.responses import FileResponse
    from pathlib import Path

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        html_path = Path(__file__).parent / "static" / "dashboard.html"
        return FileResponse(html_path)

    return app


app = create_app()
