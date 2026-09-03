"""
JARVIS AI — Mock Search Provider
Provides deterministic, offline search responses for fast, reproducible tests.
"""

from typing import Dict, List, Optional
from WEB.search.base import BaseSearchProvider, SearchResult


class MockSearchProvider(BaseSearchProvider):
    """Deterministic in-memory search provider for unit testing."""

    def __init__(self, predefined_results: Optional[Dict[str, List[SearchResult]]] = None):
        super().__init__(name="mock")
        self._results: Dict[str, List[SearchResult]] = predefined_results or {}

    def is_available(self) -> bool:
        return True

    def set_results_for_query(self, query: str, results: List[SearchResult]):
        """Inject canned test responses for a specific query."""
        self._results[query.lower().strip()] = results

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        q = query.lower().strip()
        if q in self._results:
            return self._results[q][:max_results]

        # Return reasonable default synthesized mock results
        return [
            SearchResult(
                url=f"https://example.org/docs/{q.replace(' ', '-')}",
                title=f"Official Documentation: {query.title()}",
                snippet=f"Detailed reference, benchmarks, and installation guide for {query}.",
                source_type="official_docs",
                relevance_score=0.95,
            ),
            SearchResult(
                url=f"https://github.com/topics/{q.replace(' ', '-')}",
                title=f"GitHub Community & Ecosystem for {query.title()}",
                snippet=f"Open source activity, release notes, and community adoption metrics for {query}.",
                source_type="repository",
                relevance_score=0.85,
            ),
        ][:max_results]
