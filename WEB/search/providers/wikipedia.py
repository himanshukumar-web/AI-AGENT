"""
JARVIS AI — Wikipedia Search Provider
Direct high-authority encyclopedic search via Wikipedia OpenSearch and Summary APIs.
"""

from typing import List
from urllib.parse import quote
import requests

from WEB.search.base import BaseSearchProvider, SearchResult


class WikipediaSearchProvider(BaseSearchProvider):
    """Authoritative encyclopedic reference provider."""

    def __init__(self):
        super().__init__(name="wikipedia")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JarvisAIResearchBot/1.0 (https://github.com/himanshukumar-web/AI-AGENT)",
            "Accept": "application/json",
        })

    def is_available(self) -> bool:
        return True

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not query or not query.strip():
            return results

        clean_query = query.strip()

        # Step 1: Query OpenSearch API for matching page titles and links
        try:
            opensearch_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": clean_query,
                "limit": str(max_results),
                "namespace": "0",
                "format": "json",
            }
            resp = self.session.get(opensearch_url, params=params, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) >= 4:
                    titles = data[1]
                    descriptions = data[2]
                    links = data[3]
                    for i in range(len(titles)):
                        t = titles[i]
                        desc = descriptions[i] if i < len(descriptions) else ""
                        link = links[i] if i < len(links) else ""
                        if link:
                            results.append(
                                SearchResult(
                                    url=link,
                                    title=f"{t} — Wikipedia",
                                    snippet=desc or f"Wikipedia encyclopedic entry on {t}.",
                                    source_type="academic",
                                    relevance_score=0.88,
                                )
                            )
        except Exception:
            pass

        # Step 2: If OpenSearch yielded no items, attempt direct page summary
        if not results:
            try:
                first_term = clean_query.replace(" ", "_")
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(first_term)}"
                resp = self.session.get(summary_url, timeout=2.5)
                if resp.status_code == 200:
                    summary_data = resp.json()
                    extract = summary_data.get("extract")
                    page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page")
                    title = summary_data.get("title", clean_query)
                    if page_url and extract:
                        results.append(
                            SearchResult(
                                url=page_url,
                                title=f"{title} — Wikipedia",
                                snippet=extract,
                                source_type="academic",
                                relevance_score=0.90,
                            )
                        )
            except Exception:
                pass

        return results
