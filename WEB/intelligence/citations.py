"""
JARVIS AI — Source Citation & Reference Engine
Manages verified numerical citations, cross-links claims to real sources, and prevents hallucinations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse
from WEB.search.base import SearchResult


@dataclass
class Citation:
    """Individual verified source reference."""
    index: int
    url: str
    title: str
    domain: str
    source_type: str
    retrieved_time: str


class CitationManager:
    """Assigns, tracks, and formats grounded citations without fabricating sources."""

    def __init__(self):
        self._citations: Dict[str, Citation] = {}
        self._url_to_index: Dict[str, int] = {}
        self._counter: int = 1

    def reset(self):
        """Clear citations for a new research session."""
        self._citations.clear()
        self._url_to_index.clear()
        self._counter = 1

    def register_source(self, source: SearchResult) -> int:
        """Register a retrieved search result as an authentic cited source."""
        if not source or not source.url:
            return 0

        clean_url = source.url.strip().rstrip("/")
        if clean_url in self._url_to_index:
            return self._url_to_index[clean_url]

        idx = self._counter
        domain = source.domain
        if not domain:
            try:
                domain = urlparse(clean_url).netloc.replace("www.", "")
            except Exception:
                domain = ""

        cit = Citation(
            index=idx,
            url=clean_url,
            title=source.title or domain or f"Source {idx}",
            domain=domain,
            source_type=source.source_type,
            retrieved_time=source.retrieved_time,
        )

        self._citations[clean_url] = cit
        self._url_to_index[clean_url] = idx
        self._counter += 1
        return idx

    def get_citation_tag(self, url: str) -> str:
        """Return formatted bracketed citation marker like '[1]' for a URL."""
        clean_url = url.strip().rstrip("/")
        idx = self._url_to_index.get(clean_url)
        return f"[{idx}]" if idx else ""

    def get_citation_by_index(self, index: int) -> Optional[Citation]:
        for c in self._citations.values():
            if c.index == index:
                return c
        return None

    def list_citations(self) -> List[Citation]:
        return sorted(list(self._citations.values()), key=lambda c: c.index)

    def format_sources_section(self) -> str:
        """Format the full numbered references section."""
        citations = self.list_citations()
        if not citations:
            return "No external citations recorded."

        lines = ["### Sources & References"]
        for c in citations:
            lines.append(f"[{c.index}] **{c.title}** — {c.domain}  \n    <{c.url}>")

        return "\n\n".join(lines)


# Global singleton instance
citation_manager = CitationManager()
