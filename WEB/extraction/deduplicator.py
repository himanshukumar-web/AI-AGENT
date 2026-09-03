"""
JARVIS AI — Source Deduplication Layer
Identifies duplicate URLs, canonical redirects, near-duplicate pages, and syndicated copycats.
"""

from typing import List, Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from WEB.search.base import SearchResult


class SourceDeduplicator:
    """Detects and eliminates duplicate or syndicated sources."""

    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "msclkid", "ref", "source", "ref_src", "feature"
    }

    def normalize_url(self, url: str) -> str:
        """Strip tracking query parameters, hashes, and canonicalize URL formatting."""
        if not url:
            return ""
        try:
            parsed = urlparse(url.strip())
            # Clean query parameters
            query_dict = parse_qs(parsed.query, keep_blank_values=False)
            filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in self.TRACKING_PARAMS}
            clean_query = urlencode(filtered_query, doseq=True)

            # Lowercase netloc and strip port 80/443
            netloc = parsed.netloc.lower()
            if netloc.endswith(":80"):
                netloc = netloc[:-3]
            elif netloc.endswith(":443"):
                netloc = netloc[:-4]

            path = parsed.path.rstrip("/")
            if not path:
                path = "/"

            cleaned = urlunparse((
                parsed.scheme.lower() or "https",
                netloc,
                path,
                "",  # params
                clean_query,
                ""   # fragment
            ))
            return cleaned.rstrip("/")
        except Exception:
            return url.strip().rstrip("/")

    def get_shingles(self, text: str, k: int = 3) -> Set[str]:
        """Convert text into k-gram word shingles."""
        words = [w.lower() for w in text.split() if len(w) > 2]
        if len(words) < k:
            return set(words)
        return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity coefficient between two texts using word shingles."""
        if not text1 or not text2:
            return 0.0
        if text1.strip() == text2.strip():
            return 1.0

        shingles1 = self.get_shingles(text1)
        shingles2 = self.get_shingles(text2)

        if not shingles1 or not shingles2:
            return 0.0

        intersection = len(shingles1.intersection(shingles2))
        union = len(shingles1.union(shingles2))

        return float(intersection) / float(union) if union > 0 else 0.0

    def deduplicate(
        self,
        sources: List[SearchResult],
        similarity_threshold: float = 0.70
    ) -> List[SearchResult]:
        """
        Deduplicate list of search results by normalized URL and content similarity.
        Preserves the higher-scoring primary source when near-duplicates or syndications occur.
        """
        if not sources:
            return []

        # Sort sources by relevance / authority score descending
        sorted_sources = sorted(sources, key=lambda s: s.relevance_score, reverse=True)

        unique_sources: List[SearchResult] = []
        seen_norm_urls: Set[str] = set()

        for candidate in sorted_sources:
            norm_url = self.normalize_url(candidate.url)
            if norm_url in seen_norm_urls:
                continue

            # Check for near-duplicate content against already admitted sources
            is_near_dup = False
            candidate_text = candidate.snippet + " " + (candidate.title or "")
            for existing in unique_sources:
                existing_text = existing.snippet + " " + (existing.title or "")
                sim = self.calculate_similarity(candidate_text, existing_text)
                if sim >= similarity_threshold:
                    is_near_dup = True
                    break

            if not is_near_dup:
                seen_norm_urls.add(norm_url)
                unique_sources.append(candidate)

        return unique_sources


# Global singleton instance
source_deduplicator = SourceDeduplicator()
