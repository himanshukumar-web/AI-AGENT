"""
JARVIS AI — Research Rate Limiter & Resource Governor
Enforces limits on search queries, page scrapes, source count, and overall execution time.
"""

import time
from typing import Tuple
from config import MAX_SEARCHES, MAX_SOURCES, MAX_PAGE_FETCHES, MAX_RESEARCH_TIME


class ResearchRateLimiter:
    """Safeguards resources against unbounded search loops, excessive scraping, or network thrashing."""

    def __init__(
        self,
        max_searches: int = MAX_SEARCHES,
        max_sources: int = MAX_SOURCES,
        max_page_fetches: int = MAX_PAGE_FETCHES,
        max_research_time: float = MAX_RESEARCH_TIME,
        max_retries: int = 3,
    ):
        self.max_searches = max_searches
        self.max_sources = max_sources
        self.max_page_fetches = max_page_fetches
        self.max_research_time = max_research_time
        self.max_retries = max_retries

        self._searches_count = 0
        self._sources_count = 0
        self._fetches_count = 0
        self._start_time = time.perf_counter()

    def start_session(self):
        """Reset counters for a fresh research session."""
        self._searches_count = 0
        self._sources_count = 0
        self._fetches_count = 0
        self._start_time = time.perf_counter()

    def can_search(self) -> Tuple[bool, str]:
        """Check whether another search query may be executed."""
        if self._searches_count >= self.max_searches:
            return False, f"Maximum search query limit ({self.max_searches}) reached."
        if self._is_time_exceeded():
            return False, f"Maximum research duration ({self.max_research_time}s) exceeded."
        return True, ""

    def record_search(self):
        self._searches_count += 1

    def can_fetch_page(self) -> Tuple[bool, str]:
        """Check whether another web page may be scraped/fetched."""
        if self._fetches_count >= self.max_page_fetches:
            return False, f"Maximum page fetch limit ({self.max_page_fetches}) reached."
        if self._is_time_exceeded():
            return False, f"Maximum research duration ({self.max_research_time}s) exceeded."
        return True, ""

    def record_page_fetch(self):
        self._fetches_count += 1

    def can_add_source(self) -> Tuple[bool, str]:
        """Check whether another source can be admitted."""
        if self._sources_count >= self.max_sources:
            return False, f"Maximum source collection limit ({self.max_sources}) reached."
        return True, ""

    def record_source(self):
        self._sources_count += 1

    def _is_time_exceeded(self) -> bool:
        elapsed = time.perf_counter() - self._start_time
        return elapsed >= self.max_research_time

    def get_stats(self) -> dict:
        return {
            "searches_used": self._searches_count,
            "max_searches": self.max_searches,
            "fetches_used": self._fetches_count,
            "max_fetches": self.max_page_fetches,
            "sources_used": self._sources_count,
            "max_sources": self.max_sources,
            "elapsed_seconds": round(time.perf_counter() - self._start_time, 2),
            "max_seconds": self.max_research_time,
        }


# Global singleton instance
research_rate_limiter = ResearchRateLimiter()
