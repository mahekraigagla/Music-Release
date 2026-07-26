"""
NextDrop – Lookup Tables (Genre, Mood, Language)
-------------------------------------------------
These normalized tables replace plain-text categorical strings, preventing
typo anomalies and enabling efficient integer FK joins at query time.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    songs: Mapped[list["Song"]] = relationship("Song", back_populates="genre")  # noqa: F821
    market_trends: Mapped[list["MarketTrend"]] = relationship("MarketTrend", back_populates="genre")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name={self.name!r}>"


class Mood(Base):
    __tablename__ = "moods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    songs: Mapped[list["Song"]] = relationship("Song", back_populates="mood")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Mood id={self.id} name={self.name!r}>"


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    songs: Mapped[list["Song"]] = relationship("Song", back_populates="language")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Language id={self.id} code={self.code!r} name={self.name!r}>"
