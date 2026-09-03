"""
JARVIS AI — Search Abstraction Base Layer
Defines provider-independent search contracts, query representations, and source result models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class SearchResult:
    """Standardized representation of an external web source or search result."""
    url: str
    title: str
    snippet: str
    domain: str = ""
    publication_date: Optional[str] = None
    retrieved_time: str = field(default_factory=lambda: datetime.now().isoformat())
    source_type: str = "webpage"  # official_docs, academic, news, reference, blog, repository
    relevance_score: float = 0.5
    raw_content: Optional[str] = None

    def __post_init__(self):
        if not self.domain and self.url:
            try:
                parsed = urlparse(self.url)
                self.domain = parsed.netloc.lower().replace("www.", "")
            except Exception:
                self.domain = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SearchQuery:
    """Targeted sub-query generated during research planning."""
    query: str
    intent: str = "general"
    subtopic: str = ""
    priority: int = 1


class BaseSearchProvider(ABC):
    """Abstract search provider interface for interchangeable search backends."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is operational and credentials/dependencies exist."""
        pass

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute search and return list of standardized SearchResults."""
        pass
