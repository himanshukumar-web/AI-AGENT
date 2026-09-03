"""
JARVIS AI — DuckDuckGo Search Provider
Safe, zero-API-key search provider querying DuckDuckGo HTML and Instant Answer endpoints.
"""

from typing import List
from urllib.parse import parse_qs, unquote, urlparse
import requests
from bs4 import BeautifulSoup

from WEB.search.base import BaseSearchProvider, SearchResult


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """Zero-key search provider using DuckDuckGo web endpoints."""

    def __init__(self):
        super().__init__(name="duckduckgo")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

    def is_available(self) -> bool:
        """DuckDuckGo is available whenever HTTP requests can be made."""
        return True

    def _extract_target_url(self, raw_href: str) -> str:
        """Decode redirected target URL from DuckDuckGo redirect link."""
        if not raw_href:
            return ""
        if raw_href.startswith("//"):
            raw_href = "https:" + raw_href
        if "duckduckgo.com/l/?" in raw_href or "uddg=" in raw_href:
            try:
                parsed = urlparse(raw_href)
                query_params = parse_qs(parsed.query)
                if "uddg" in query_params:
                    return unquote(query_params["uddg"][0])
            except Exception:
                pass
        return raw_href

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not query or not query.strip():
            return results

        clean_query = query.strip()

        # Step 1: Query DuckDuckGo HTML endpoint
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {"q": clean_query, "b": ""}
            resp = self.session.post(url, data=data, timeout=4.0)

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                web_results = soup.select(".result")

                for item in web_results:
                    if len(results) >= max_results:
                        break

                    # Skip ad slots or empty result containers
                    if "result--ad" in item.get("class", []):
                        continue

                    title_el = item.select_one(".result__title a")
                    snippet_el = item.select_one(".result__snippet")

                    if not title_el or not snippet_el:
                        continue

                    raw_href = title_el.get("href", "")
                    target_url = self._extract_target_url(raw_href)
                    if not target_url or not target_url.startswith("http"):
                        continue

                    title = title_el.get_text().strip()
                    snippet = snippet_el.get_text().strip()

                    results.append(
                        SearchResult(
                            url=target_url,
                            title=title,
                            snippet=snippet,
                            source_type="webpage",
                            relevance_score=0.75,
                        )
                    )
        except Exception:
            pass

        # Step 2: If HTML endpoint was rate-limited or empty, try Instant Answer API
        if not results:
            try:
                api_url = "https://api.duckduckgo.com/"
                params = {"q": clean_query, "format": "json", "no_html": "1", "skip_disambig": "1"}
                resp = self.session.get(api_url, params=params, timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json()
                    abstract_url = data.get("AbstractURL")
                    abstract_text = data.get("AbstractText")
                    heading = data.get("Heading")
                    if abstract_url and abstract_text:
                        results.append(
                            SearchResult(
                                url=abstract_url,
                                title=heading or clean_query,
                                snippet=abstract_text,
                                source_type="reference",
                                relevance_score=0.85,
                            )
                        )
                    for topic in data.get("RelatedTopics", []):
                        if len(results) >= max_results:
                            break
                        first_url = topic.get("FirstURL")
                        topic_text = topic.get("Text")
                        if first_url and topic_text:
                            results.append(
                                SearchResult(
                                    url=first_url,
                                    title=topic_text.split(" - ")[0] if " - " in topic_text else clean_query,
                                    snippet=topic_text,
                                    source_type="reference",
                                    relevance_score=0.70,
                                )
                            )
            except Exception:
                pass

        return results
