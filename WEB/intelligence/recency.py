"""
JARVIS AI — Recency & Temporal Intelligence Layer
Detects time-sensitive intents and distinguishes publication dates, event dates, and retrieval times.
"""

from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple


class RecencyAnalyzer:
    """Evaluates time sensitivity of research topics and dates of sources."""

    TIME_SENSITIVE_INDICATORS = [
        "latest", "current", "today", "yesterday", "recent", "recently",
        "newest", "up to date", "trends", "forecast", "roadmap",
        "2026", "this year", "this month", "release notes", "version",
    ]

    def is_time_sensitive(self, query: str) -> bool:
        """Determine if query demands up-to-date, current information."""
        if not query:
            return False
        q = query.lower()
        return any(ind in q for ind in self.TIME_SENSITIVE_INDICATORS)

    def extract_dates(self, text: str) -> List[str]:
        """Extract explicit calendar years or dates from text."""
        if not text:
            return []
        dates = []
        # Match YYYY-MM-DD or DD Month YYYY or 2020-2026
        matches_iso = re.findall(r"\b(202[0-6]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))\b", text)
        dates.extend(matches_iso)

        matches_year = re.findall(r"\b(202[0-6]|201\d)\b", text)
        for y in matches_year:
            if y not in dates:
                dates.append(y)

        return dates

    def categorize_dates(
        self,
        pub_date: Optional[str] = None,
        retrieved_time: Optional[str] = None,
        content_text: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        """
        Distinguish publication date, event date, and retrieval timestamp.
        Avoids presenting old information as current.
        """
        now_str = retrieved_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        event_date = None
        if content_text:
            extracted = self.extract_dates(content_text[:600])
            if extracted:
                event_date = extracted[0]

        return {
            "publication_date": pub_date,
            "event_date": event_date,
            "retrieved_date": now_str,
        }

    def evaluate_staleness(self, query: str, detected_year: Optional[str]) -> Tuple[bool, str]:
        """
        Check whether source information might be stale for the query.
        Current system reference year is 2026.
        """
        if not self.is_time_sensitive(query) or not detected_year:
            return False, "Not time-sensitive or date not identified."

        try:
            year_int = int(re.search(r"\b(\d{4})\b", detected_year).group(1))
            if year_int < 2025:
                return True, f"Source date ({year_int}) may be outdated for current 2026 information."
            return False, f"Source date ({year_int}) is sufficiently recent."
        except Exception:
            return False, "Could not evaluate staleness."


# Global singleton instance
recency_analyzer = RecencyAnalyzer()
