"""
JARVIS AI — Source Quality Scoring Engine
Scores web sources by domain authority, relevance, recency, and evidence depth.
"""

from dataclasses import dataclass
import re
from typing import Optional
from urllib.parse import urlparse
from WEB.search.base import SearchResult


@dataclass
class SourceQualityScore:
    """Multi-factor quality rating of an information source."""
    authority_score: float
    relevance_score: float
    recency_score: float
    evidence_score: float
    overall_score: float
    tier: str  # "High Authority", "Reputable", "Secondary", "Low Authority"


class SourceQualityScorer:
    """Evaluates the reliability, expertise, and authority of external web sources."""

    HIGH_AUTHORITY_DOMAINS = {
        "wikipedia.org", "python.org", "github.com", "arxiv.org",
        "nih.gov", "cdc.gov", "nasa.gov", "w3.org", "mozilla.org",
        "huggingface.co", "pytorch.org", "tensorflow.org", "apache.org",
        "microsoft.com", "google.com", "apple.com", "openai.com", "anthropic.com",
    }

    REPUTABLE_DOMAINS = {
        "reuters.com", "apnews.com", "bbc.com", "bloomberg.com",
        "nature.com", "science.org", "ieee.org", "acm.org",
        "arstechnica.com", "techcrunch.com", "theverge.com", "wired.com",
        "stackoverflow.com", "stackexchange.com", "infoq.com", "zdnet.com",
    }

    LOWER_AUTHORITY_DOMAINS = {
        "medium.com", "dev.to", "quora.com", "reddit.com", "tumblr.com",
        "pinterest.com", "blogspot.com", "wordpress.com", "geeksforgeeks.org",
    }

    def score_source(
        self,
        source: SearchResult,
        query: str = "",
        content_text: Optional[str] = None
    ) -> SourceQualityScore:
        """Calculate multi-dimensional score for a source."""
        domain = source.domain.lower()
        if not domain and source.url:
            try:
                domain = urlparse(source.url).netloc.lower().replace("www.", "")
            except Exception:
                domain = ""

        # 1. Authority Scoring
        auth_score = 0.50
        if any(domain.endswith(tld) for tld in [".gov", ".edu", ".ac.uk", ".int"]):
            auth_score = 0.95
        elif domain.startswith("docs.") or domain.startswith("developer.") or domain.startswith("api."):
            auth_score = 0.92
        elif any(domain == d or domain.endswith("." + d) for d in self.HIGH_AUTHORITY_DOMAINS):
            auth_score = 0.90
        elif any(domain == d or domain.endswith("." + d) for d in self.REPUTABLE_DOMAINS):
            auth_score = 0.78
        elif any(domain == d or domain.endswith("." + d) for d in self.LOWER_AUTHORITY_DOMAINS):
            auth_score = 0.40

        # Adjust for source type
        if source.source_type == "official_docs":
            auth_score = max(auth_score, 0.95)
        elif source.source_type == "academic":
            auth_score = max(auth_score, 0.88)

        # 2. Relevance Scoring
        rel_score = source.relevance_score
        if query:
            q_terms = [t.lower() for t in query.split() if len(t) > 2]
            title_lower = (source.title or "").lower()
            snippet_lower = (source.snippet or "").lower()
            body_lower = (content_text or "").lower()

            matches = 0
            for term in q_terms:
                if term in title_lower:
                    matches += 2
                if term in snippet_lower:
                    matches += 1
                if term in body_lower:
                    matches += 1

            max_possible = max(len(q_terms) * 3, 1)
            rel_score = min(max(float(matches) / float(max_possible), 0.3), 1.0)

        # 3. Recency Scoring
        rec_score = 0.65
        date_str = source.publication_date or ""
        if not date_str and content_text:
            m = re.search(r"\b(202[0-6]|201\d)\b", content_text[:500])
            if m:
                date_str = m.group(1)

        if "2026" in date_str:
            rec_score = 1.0
        elif "2025" in date_str:
            rec_score = 0.90
        elif "2024" in date_str:
            rec_score = 0.78
        elif "2023" in date_str:
            rec_score = 0.65
        elif any(y in date_str for y in ["2022", "2021", "2020"]):
            rec_score = 0.50

        # 4. Evidence Depth Scoring
        ev_score = 0.50
        body = content_text or source.snippet or ""
        word_count = len(body.split())
        if word_count > 500:
            ev_score = 0.90
        elif word_count > 200:
            ev_score = 0.75
        elif word_count > 50:
            ev_score = 0.60
        else:
            ev_score = 0.40

        # Weighted aggregate: 40% Authority, 30% Relevance, 15% Recency, 15% Evidence
        overall = (0.40 * auth_score) + (0.30 * rel_score) + (0.15 * rec_score) + (0.15 * ev_score)
        overall = round(overall, 3)

        if auth_score >= 0.88:
            tier = "High Authority"
        elif auth_score >= 0.70:
            tier = "Reputable"
        elif auth_score >= 0.50:
            tier = "Secondary"
        else:
            tier = "Low Authority"

        return SourceQualityScore(
            authority_score=round(auth_score, 2),
            relevance_score=round(rel_score, 2),
            recency_score=round(rec_score, 2),
            evidence_score=round(ev_score, 2),
            overall_score=overall,
            tier=tier,
        )


# Global singleton instance
source_scorer = SourceQualityScorer()
