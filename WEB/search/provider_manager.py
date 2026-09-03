"""
JARVIS AI — Search Provider Manager
Coordinates search providers, manages failover chains, and executes multi-query searches.
"""

from typing import Dict, List, Optional
from config import DEFAULT_SEARCH_PROVIDER
from WEB.search.base import BaseSearchProvider, SearchResult
from WEB.search.providers.duckduckgo import DuckDuckGoSearchProvider
from WEB.search.providers.wikipedia import WikipediaSearchProvider
from WEB.search.providers.browser import BrowserSearchProvider
from WEB.search.providers.mock import MockSearchProvider


class SearchProviderManager:
    """Central orchestrator for provider-independent web search."""

    def __init__(self):
        self._providers: Dict[str, BaseSearchProvider] = {}
        self._active_provider_name: str = DEFAULT_SEARCH_PROVIDER
        self._register_default_providers()

    def _register_default_providers(self):
        """Initialize standard built-in providers."""
        self.register_provider(DuckDuckGoSearchProvider())
        self.register_provider(WikipediaSearchProvider())
        self.register_provider(BrowserSearchProvider())
        self.register_provider(MockSearchProvider())

    def register_provider(self, provider: BaseSearchProvider):
        """Register a search provider."""
        self._providers[provider.name.lower()] = provider

    def get_provider(self, name: str) -> Optional[BaseSearchProvider]:
        """Retrieve a specific registered provider."""
        return self._providers.get(name.lower())

    def list_providers(self) -> List[str]:
        """List registered provider names."""
        return list(self._providers.keys())

    def set_active_provider(self, name: str) -> bool:
        """Set active search provider."""
        clean = name.lower().strip()
        if clean in self._providers or clean == "auto":
            self._active_provider_name = clean
            return True
        return False

    def get_active_provider_name(self) -> str:
        return self._active_provider_name

    def search(
        self,
        query: str,
        max_results: int = 5,
        provider_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Execute search using requested provider or auto-fallback chain.
        Fallback order: Requested/Active -> DuckDuckGo -> Wikipedia -> Browser -> Mock.
        Checks TTL cache before making network calls.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()

        # Check TTL cache
        try:
            from WEB.security.caching import research_cache
            cached = research_cache.get_search_results(clean_query)
            if cached:
                return cached[:max_results]
        except Exception:
            pass

        target_name = (provider_name or self._active_provider_name).lower()

        # Direct provider requested
        if target_name != "auto" and target_name in self._providers:
            prov = self._providers[target_name]
            if prov.is_available():
                try:
                    res = prov.search(clean_query, max_results=max_results)
                    if res:
                        try:
                            from WEB.security.caching import research_cache
                            research_cache.set_search_results(clean_query, res)
                        except Exception:
                            pass
                        return res
                except Exception:
                    pass

        # Fallback priority chain
        chain = ["duckduckgo", "wikipedia", "browser", "mock"]
        for p_name in chain:
            if p_name == target_name:
                continue
            prov = self._providers.get(p_name)
            if prov and prov.is_available():
                try:
                    res = prov.search(clean_query, max_results=max_results)
                    if res:
                        try:
                            from WEB.security.caching import research_cache
                            research_cache.set_search_results(clean_query, res)
                        except Exception:
                            pass
                        return res
                except Exception:
                    continue

        return []

    def multi_search(
        self,
        queries: List[str],
        max_results_per_query: int = 3,
        provider_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """Execute searches across multiple generated queries and combine results."""
        combined: List[SearchResult] = []
        seen_urls = set()

        for q in queries:
            if not q or not q.strip():
                continue
            results = self.search(q, max_results=max_results_per_query, provider_name=provider_name)
            for item in results:
                norm_url = item.url.lower().rstrip("/")
                if norm_url not in seen_urls:
                    seen_urls.add(norm_url)
                    combined.append(item)

        return combined


# Global singleton instance
search_provider_manager = SearchProviderManager()
