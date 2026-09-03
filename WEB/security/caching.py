"""
JARVIS AI — Research Cache Engine
Provides TTL-governed in-memory & persistent caching for search queries and page extracts.
"""

from datetime import datetime, timedelta
import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from config import RESEARCH_CACHE_TTL
from WEB.search.base import SearchResult


class ResearchCache:
    """High-performance TTL cache preventing duplicate network lookups."""

    def __init__(self, default_ttl: int = RESEARCH_CACHE_TTL):
        self.default_ttl = default_ttl
        self._search_cache: Dict[str, Dict[str, Any]] = {}
        self._page_cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.strip().lower().encode("utf-8")).hexdigest()

    def get_search_results(self, query: str) -> Optional[List[SearchResult]]:
        """Retrieve unexpired cached search results for a query."""
        h_key = self._hash_key(query)
        entry = self._search_cache.get(h_key)
        if not entry:
            self._misses += 1
            return None

        if time.time() > entry["expires_at"]:
            del self._search_cache[h_key]
            self._misses += 1
            return None

        self._hits += 1
        return [SearchResult.from_dict(d) for d in entry["data"]]

    def set_search_results(
        self,
        query: str,
        results: List[SearchResult],
        ttl: Optional[int] = None
    ):
        """Store search results with expiration timestamp."""
        h_key = self._hash_key(query)
        actual_ttl = ttl if ttl is not None else self.default_ttl
        self._search_cache[h_key] = {
            "expires_at": time.time() + actual_ttl,
            "data": [r.to_dict() for r in results],
            "query": query,
        }

    def get_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve unexpired cached page content."""
        h_key = self._hash_key(url)
        entry = self._page_cache.get(h_key)
        if not entry:
            self._misses += 1
            return None

        if time.time() > entry["expires_at"]:
            del self._page_cache[h_key]
            self._misses += 1
            return None

        self._hits += 1
        return entry["data"]

    def set_page_content(
        self,
        url: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """Store extracted page content."""
        h_key = self._hash_key(url)
        actual_ttl = ttl if ttl is not None else self.default_ttl
        self._page_cache[h_key] = {
            "expires_at": time.time() + actual_ttl,
            "data": data,
            "url": url,
        }

    def clear_cache(self):
        """Flush all cached searches and pages."""
        self._search_cache.clear()
        self._page_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "cached_searches": len(self._search_cache),
            "cached_pages": len(self._page_cache),
            "cache_hits": self._hits,
            "cache_misses": self._misses,
            "default_ttl_seconds": self.default_ttl,
        }


# Global singleton instance
research_cache = ResearchCache()
