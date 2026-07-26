"""
NextDrop – Database Engine & Session Factory
---------------------------------------------
Provides:
  - Async SQLAlchemy engine (AsyncSession) for FastAPI request handlers.
  - Sync engine for Alembic migrations and Celery tasks.
  - `get_db()` – async dependency injected into route handlers.
  - `Base`     – declarative base shared by all ORM models.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


# ---------------------------------------------------------------------------
# Async Engine (FastAPI / application runtime)
# ---------------------------------------------------------------------------
async_engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,      # Reconnect on stale connections
    echo=settings.debug,     # Log SQL in development only
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a transactional AsyncSession.
    Rolls back on exception, always closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Sync Engine (Alembic migrations, Celery tasks)
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine  # noqa: E402

sync_engine = create_engine(
    settings.database_sync_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
    future=True,
)


# ---------------------------------------------------------------------------
# Startup / Shutdown helpers
# ---------------------------------------------------------------------------
async def init_db() -> None:
    """Called on application startup to verify the DB connection."""
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    """Called on application shutdown to cleanly dispose the engine pool."""
    await async_engine.dispose()
