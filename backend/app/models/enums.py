"""
NextDrop – Shared Enums
------------------------
Python-native enumerations used by SQLAlchemy models and Pydantic schemas.
"""

from enum import Enum


class ReleaseStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    released = "released"


class ReleaseType(str, Enum):
    single = "single"
    ep = "ep"
    album = "album"


class ArtistGoal(str, Enum):
    maximum_streams = "Maximum Streams"
    maximum_revenue = "Maximum Revenue"
    audience_growth = "Audience Growth"
    playlist_reach = "Playlist Reach"


class TrainingJobStatus(str, Enum):
    pending = "PENDING"
    running = "RUNNING"
    success = "SUCCESS"
    failed = "FAILED"


class DatasetType(str, Enum):
    spotify_tracks = "spotify_tracks"
    spotify_charts = "spotify_charts"
    lastfm_tags = "lastfm_tags"
    musicbrainz_releases = "musicbrainz_releases"
