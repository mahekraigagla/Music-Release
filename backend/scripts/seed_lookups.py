"""
NextDrop – Lookup Table Seed Script
--------------------------------------
Seeds the `genres`, `moods`, `languages`, `platforms`, `countries`,
and `time_slots` tables with production baseline data.

Run after applying Alembic migrations:
    python -m scripts.seed_lookups

This script is idempotent: running it twice will not create duplicates.
"""

from __future__ import annotations

import sys
import os

# Add the backend/ directory to sys.path so `app` is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.core.database import sync_engine
from app.models.lookups import Genre, Mood, Language
from app.models.platform import Platform, Country
from app.models.timeslot import TimeSlot


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------
GENRES = [
    "Pop", "Hip-Hop", "R&B", "Electronic", "Dance", "Rock", "Indie",
    "Synthwave", "Jazz", "Classical", "Metal", "Country", "Reggaeton",
    "Afrobeats", "Latin", "K-Pop", "Soul", "Folk", "Punk", "Blues",
    "Ambient", "Trap", "Drill", "Lo-Fi", "Gospel", "Reggae",
]

MOODS = [
    "Energetic", "Melancholic", "Happy", "Calm", "Romantic", "Aggressive",
    "Motivational", "Chill", "Dark", "Uplifting", "Nostalgic", "Anxious",
    "Euphoric", "Sad", "Dreamy", "Party",
]

LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "de", "name": "German"},
    {"code": "hi", "name": "Hindi"},
    {"code": "ko", "name": "Korean"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ar", "name": "Arabic"},
    {"code": "it", "name": "Italian"},
    {"code": "tr", "name": "Turkish"},
    {"code": "nl", "name": "Dutch"},
    {"code": "zh", "name": "Chinese"},
    {"code": "ru", "name": "Russian"},
    {"code": "sv", "name": "Swedish"},
    {"code": "unknown", "name": "Unknown"},
]

# Payout rates in USD per stream (approximate industry averages, 2024)
PLATFORMS = [
    {"name": "spotify",      "payout_rate": 0.003500, "growth_rate": 1.08},
    {"name": "apple_music",  "payout_rate": 0.007300, "growth_rate": 1.05},
    {"name": "youtube",      "payout_rate": 0.000690, "growth_rate": 1.15},
    {"name": "amazon_music", "payout_rate": 0.004000, "growth_rate": 1.10},
    {"name": "tidal",        "payout_rate": 0.012500, "growth_rate": 1.03},
    {"name": "deezer",       "payout_rate": 0.006400, "growth_rate": 1.04},
]

# Top streaming markets
COUNTRIES = [
    {"code": "US", "name": "United States",   "cpm_multiplier": 1.50, "market_growth_rate": 1.05},
    {"code": "GB", "name": "United Kingdom",  "cpm_multiplier": 1.30, "market_growth_rate": 1.04},
    {"code": "DE", "name": "Germany",         "cpm_multiplier": 1.25, "market_growth_rate": 1.04},
    {"code": "FR", "name": "France",          "cpm_multiplier": 1.20, "market_growth_rate": 1.03},
    {"code": "BR", "name": "Brazil",          "cpm_multiplier": 0.70, "market_growth_rate": 1.12},
    {"code": "MX", "name": "Mexico",          "cpm_multiplier": 0.65, "market_growth_rate": 1.10},
    {"code": "IN", "name": "India",           "cpm_multiplier": 0.40, "market_growth_rate": 1.25},
    {"code": "AU", "name": "Australia",       "cpm_multiplier": 1.35, "market_growth_rate": 1.05},
    {"code": "CA", "name": "Canada",          "cpm_multiplier": 1.30, "market_growth_rate": 1.04},
    {"code": "JP", "name": "Japan",           "cpm_multiplier": 1.10, "market_growth_rate": 1.02},
    {"code": "KR", "name": "South Korea",     "cpm_multiplier": 1.05, "market_growth_rate": 1.06},
    {"code": "ES", "name": "Spain",           "cpm_multiplier": 1.00, "market_growth_rate": 1.04},
    {"code": "IT", "name": "Italy",           "cpm_multiplier": 1.00, "market_growth_rate": 1.03},
    {"code": "NL", "name": "Netherlands",     "cpm_multiplier": 1.20, "market_growth_rate": 1.04},
    {"code": "SE", "name": "Sweden",          "cpm_multiplier": 1.15, "market_growth_rate": 1.03},
    {"code": "NG", "name": "Nigeria",         "cpm_multiplier": 0.30, "market_growth_rate": 1.30},
    {"code": "ZA", "name": "South Africa",    "cpm_multiplier": 0.45, "market_growth_rate": 1.15},
    {"code": "AR", "name": "Argentina",       "cpm_multiplier": 0.50, "market_growth_rate": 1.08},
    {"code": "GL", "name": "Global",          "cpm_multiplier": 1.00, "market_growth_rate": 1.00},
]

# 35 time slots (7 days × 5 hours) in UTC
# Day-of-week: 1=Monday … 7=Sunday
# Hours chosen to represent: Morning, Afternoon, Late Afternoon, Evening, Night
DAY_NAMES = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
             5: "Friday", 6: "Saturday", 7: "Sunday"}
HOURS = {10: "Morning", 14: "Afternoon", 16: "Late Afternoon", 18: "Evening", 21: "Night"}

TIME_SLOTS = [
    {
        "day_of_week": day,
        "release_hour": hour,
        "timezone": "UTC",
        "slot_name": f"{DAY_NAMES[day]} {label}",
        "is_active": True,
    }
    for day in range(1, 8)
    for hour, label in HOURS.items()
]


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------
def seed(session: Session) -> None:
    print("Seeding genres...")
    for name in GENRES:
        session.execute(
            insert(Genre)
            .values(name=name)
            .on_conflict_do_nothing(index_elements=["name"])
        )

    print("Seeding moods...")
    for name in MOODS:
        session.execute(
            insert(Mood)
            .values(name=name)
            .on_conflict_do_nothing(index_elements=["name"])
        )

    print("Seeding languages...")
    for lang in LANGUAGES:
        session.execute(
            insert(Language)
            .values(**lang)
            .on_conflict_do_nothing(index_elements=["code"])
        )

    print("Seeding platforms...")
    for platform in PLATFORMS:
        session.execute(
            insert(Platform)
            .values(**platform)
            .on_conflict_do_nothing(index_elements=["name"])
        )

    print("Seeding countries...")
    for country in COUNTRIES:
        session.execute(
            insert(Country)
            .values(**country)
            .on_conflict_do_nothing(index_elements=["code"])
        )

    print("Seeding time slots (35 slots)...")
    for slot in TIME_SLOTS:
        session.execute(
            insert(TimeSlot)
            .values(**slot)
            .on_conflict_do_nothing(
                index_elements=["day_of_week", "release_hour", "timezone"]
            )
        )

    session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    with Session(sync_engine) as session:
        seed(session)
