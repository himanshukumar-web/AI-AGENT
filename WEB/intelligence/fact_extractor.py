"""
JARVIS AI — Fact & Claim Extraction Layer
Extracts structural factual assertions, entities, and evidence statements from web sources.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional
from WEB.search.base import SearchResult


@dataclass
class ExtractedClaim:
    """A structural representation of a verifiable factual claim."""
    statement: str
    entity: str
    topic: str
    source_urls: List[str] = field(default_factory=list)
    confidence: str = "Likely"  # High, Likely, Uncertain, Conflicting
    evidence_snippets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "statement": self.statement,
            "entity": self.entity,
            "topic": self.topic,
            "source_urls": self.source_urls,
            "confidence": self.confidence,
            "evidence_snippets": self.evidence_snippets,
        }


class FactExtractor:
    """Extracts factual statements and entities from text and search results."""

    CLAIM_TRIGGERS = [
        "supports", "provides", "features", "released", "announced",
        "allows", "benchmarks", "requires", "includes", "runs on",
        "developed by", "created by", "faster than", "compatible with",
        "costs", "open source", "designed for", "version", "introduces",
        "contains", "offers", "implements", "powers", "delivers", "uses",
    ]

    def extract_claims(
        self,
        sources: List[SearchResult],
        topic: str = "",
        max_claims: int = 8
    ) -> List[ExtractedClaim]:
        """Extract structured claims from source snippets and text."""
        claims: List[ExtractedClaim] = []
        seen_statements = set()

        for s in sources:
            text_corpus = (s.snippet or "") + " " + (s.raw_content or "")
            # Split into clean sentences
            sentences = re.split(r"(?<=[.!?])\s+", text_corpus)

            for sent in sentences:
                sent_clean = sent.strip().replace("\n", " ")
                # Check sentence suitability: length and assertion marker
                if len(sent_clean) < 30 or len(sent_clean) > 250:
                    continue

                sent_lower = sent_clean.lower()
                if any(trig in sent_lower for trig in self.CLAIM_TRIGGERS):
                    # Dedup similar statements
                    norm_key = sent_clean[:60].lower()
                    if norm_key in seen_statements:
                        continue
                    seen_statements.add(norm_key)

                    # Determine entity
                    entity = self._detect_entity(sent_clean, s.title, topic)

                    claims.append(
                        ExtractedClaim(
                            statement=sent_clean,
                            entity=entity,
                            topic=topic or "Research",
                            source_urls=[s.url],
                            confidence="Likely",
                            evidence_snippets=[sent_clean],
                        )
                    )

                    if len(claims) >= max_claims:
                        return claims

        return claims

    def _detect_entity(self, statement: str, title: str, topic: str) -> str:
        """Infer target subject/entity of the claim."""
        # Try extracting capitalized proper nouns
        caps = re.findall(r"\b[A-Z][a-zA-Z0-9_\.\-]+\b", statement)
        if caps:
            return caps[0]
        if topic:
            return topic.split()[0]
        if title:
            return title.split()[0]
        return "General"


# Global singleton instance
fact_extractor = FactExtractor()
