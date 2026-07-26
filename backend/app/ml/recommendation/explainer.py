"""
NextDrop – Recommendation Strategy Explainer
----------------------------------------------
Generates artist-friendly strategy breakdowns, music term translation,
and tactical promotion checklists tailored to song characteristics.
"""

from __future__ import annotations

from typing import Any

MUSIC_FEATURE_LABELS = {
    "speechiness": "Vocal Density",
    "acousticness": "Acoustic Warmth",
    "duration_ms": "Song Length",
    "loudness": "Production Punch",
    "energy": "Track Energy",
    "liveness": "Live Vibe",
    "valence": "Track Feel (Mood)",
    "tempo": "Song Speed (BPM)",
    "mode": "Harmonic Mode",
    "danceability": "Rhythmic Bounce",
    "rhythmic_potency": "Groove Impact",
    "emotional_intensity": "Emotional Power",
    "acoustic_energy_ratio": "Dynamic Balance",
    "listener_velocity": "Fan Engagement",
    "previous_avg_streams": "Catalog Momentum",
}


class StrategyExplainer:
    """Artist-friendly release strategy explainer."""

    def generate_strategy_report(
        self,
        song_title: str,
        artist_name: str,
        top_rec: dict[str, Any],
        attributions: list[dict[str, Any]],
        genre: str = "pop",
        goal: str = "Maximum Streams",
    ) -> dict[str, Any]:
        """
        Generate executive strategy summary with artist-friendly terms and dynamic checklists.
        """
        slot_name = top_rec.get("slot_name", "Friday Late Afternoon")
        rss = top_rec.get("release_strategy_score", 0.0)
        streams = top_rec.get("predicted_streams", 0)
        earnings_inr = top_rec.get("expected_earnings_inr", round(top_rec.get("expected_earnings_usd", 0.0) * 83.5, 2))
        dow = top_rec.get("day_of_week", 5)

        headline = f"Release '{song_title}' on {slot_name} for Peak Audience Reach"
        summary = (
            f"Analyzing your song's acoustic feel, fan activity, and streaming market velocity, "
            f"dropping on {slot_name} gives you a Release Score of {rss}/100. "
            f"Estimated first-week reach is {streams:,} streams (₹{earnings_inr:,.2f} INR)."
        )

        # Strategic rationale
        reasons = []
        if dow == 5:
            reasons.append("Friday is the global drop day for official playlist inclusions (Release Radar & New Music playlists).")
        elif dow == 4:
            reasons.append("Thursday night releases capture weekend excitement early and stand out before Friday competition.")
        elif dow == 6:
            reasons.append("Saturday release targets high weekend listener streaming activity.")
        else:
            reasons.append("Mid-week release minimizes direct competition from major label catalog drops.")

        # Friendly feature attributions
        translated_attributions = []
        for attr in attributions:
            raw_feat = attr.get("feature", "")
            friendly_name = MUSIC_FEATURE_LABELS.get(raw_feat, raw_feat.replace("_", " ").title())
            attr_copy = dict(attr)
            attr_copy["feature"] = friendly_name
            translated_attributions.append(attr_copy)

            if len(reasons) < 4:
                pct = attr.get("percentage_impact", 0)
                reasons.append(f"{friendly_name} drives {pct}% of your track's potential streaming velocity.")

        # Dynamic Tactical Checklist per genre & goal
        checklist = []
        genre_lower = genre.lower()

        if "pop" in genre_lower:
            checklist.append("Submit 14 days early on Spotify for Artists to pitch for Pop Rising & Pop Remix playlists.")
            checklist.append("Launch a 15-second TikTok sound teaser 4 days before release.")
        elif "hip" in genre_lower or "rap" in genre_lower:
            checklist.append("Pitch track for Most Necessary & RapCaviar placement 10 days before drop.")
            checklist.append("Host an Instagram Live pre-release countdown 1 hour before midnight drop.")
        elif "electronic" in genre_lower or "dance" in genre_lower:
            checklist.append("Distribute promo WAV files to club DJs and playlist curators 2 weeks prior.")
            checklist.append("Target Friday Night & Saturday night weekend listening playlists.")
        else:
            checklist.append("Pitch track on Spotify for Artists 14 days before release with primary genre tags.")
            checklist.append("Share behind-the-scenes studio clips across social platforms.")

        if "revenue" in goal.lower():
            checklist.append("Focus pre-save promotion on US, UK, Germany, and Japan for higher payout rates.")
        elif "reach" in goal.lower() or "growth" in goal.lower():
            checklist.append("Run a pre-save campaign with exclusive unreleased acoustic clip rewards.")
        else:
            checklist.append("Coordinate direct playlist outreach on release morning.")

        return {
            "headline": headline,
            "summary": summary,
            "key_drivers": reasons,
            "tactical_checklist": checklist,
            "translated_attributions": translated_attributions,
            "primary_slot": slot_name,
            "projected_streams": streams,
            "projected_earnings": earnings_inr,
            "rss_score": rss,
        }
