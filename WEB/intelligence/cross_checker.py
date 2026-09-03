"""
JARVIS AI — Cross-Source Verification & Disagreement Detection
Compares claims across independent sources, verifies agreement, and flags conflicting evidence.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from WEB.intelligence.fact_extractor import ExtractedClaim


@dataclass
class CrossCheckResult:
    """Consolidated outcome of cross-referencing claims across multiple sources."""
    verified_claims: List[ExtractedClaim] = field(default_factory=list)
    conflicting_claims: List[Dict[str, Any]] = field(default_factory=list)
    agreement_rate: float = 1.0
    summary: str = ""


class CrossChecker:
    """Compares claims across sources to elevate confidence or detect disputes."""

    CONTRADICTION_PAIRS = [
        ("free", "paid"), ("open source", "proprietary"),
        ("released", "unreleased"), ("deprecated", "active"),
        ("supports", "does not support"), ("faster", "slower"),
        ("supported", "unsupported"), ("yes", "no"),
    ]

    def cross_check(self, claims: List[ExtractedClaim]) -> CrossCheckResult:
        """Analyze claims across sources and identify consensus vs conflicting points."""
        if not claims:
            return CrossCheckResult(summary="No claims extracted to cross-check.")

        verified: List[ExtractedClaim] = []
        conflicts: List[Dict[str, Any]] = []

        # Group claims by entity and core topic
        grouped: Dict[str, List[ExtractedClaim]] = {}
        for c in claims:
            key = f"{c.entity.lower()}_{c.topic.lower()}"
            grouped.setdefault(key, []).append(c)

        for key, group in grouped.items():
            if len(group) == 1:
                # Single source claim -> marked as Likely
                verified.append(group[0])
                continue

            # Multi-source analysis
            has_conflict = False
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    c1 = group[i]
                    c2 = group[j]

                    conflict_detected, reason = self._detect_conflict(c1.statement, c2.statement)
                    if conflict_detected:
                        has_conflict = True
                        c1.confidence = "Conflicting"
                        c2.confidence = "Conflicting"
                        conflicts.append({
                            "entity": c1.entity,
                            "point_of_disagreement": reason,
                            "source_a_claim": c1.statement,
                            "source_a_urls": c1.source_urls,
                            "source_b_claim": c2.statement,
                            "source_b_urls": c2.source_urls,
                            "explanation": f"Sources disagree on this point: One source asserts '{c1.statement}' while another reports '{c2.statement}'."
                        })

            if not has_conflict:
                # Sources agree or complement each other -> Boost confidence to High
                merged = group[0]
                all_urls = set(merged.source_urls)
                for other in group[1:]:
                    all_urls.update(other.source_urls)
                    merged.evidence_snippets.extend(other.evidence_snippets)
                merged.source_urls = list(all_urls)
                merged.confidence = "High" if len(merged.source_urls) > 1 else "Likely"
                verified.append(merged)

        total_analyzed = len(claims)
        conflict_count = len(conflicts)
        agreement_rate = max(0.0, 1.0 - (float(conflict_count) / float(total_analyzed))) if total_analyzed > 0 else 1.0

        if conflicts:
            summary = f"Identified {conflict_count} point(s) of disagreement among sources. Consensus agreement rate: {agreement_rate * 100:.0f}%."
        else:
            summary = f"All {len(verified)} verified claims show strong cross-source agreement ({agreement_rate * 100:.0f}%)."

        return CrossCheckResult(
            verified_claims=verified,
            conflicting_claims=conflicts,
            agreement_rate=round(agreement_rate, 2),
            summary=summary,
        )

    def _detect_conflict(self, text1: str, text2: str) -> (bool, str):
        """Check for direct opposite or contradiction keywords in two assertions."""
        t1 = text1.lower()
        t2 = text2.lower()

        for term_a, term_b in self.CONTRADICTION_PAIRS:
            if (term_a in t1 and term_b in t2) or (term_b in t1 and term_a in t2):
                return True, f"Conflict between '{term_a}' vs '{term_b}'"

        # Check for conflicting years / dates for same entity
        import re
        y1 = re.findall(r"\b(202[0-9])\b", t1)
        y2 = re.findall(r"\b(202[0-9])\b", t2)
        if y1 and y2 and y1 != y2 and ("release" in t1 or "version" in t1 or "announced" in t1):
            return True, f"Conflicting years: {y1[0]} vs {y2[0]}"

        return False, ""


# Global singleton instance
cross_checker = CrossChecker()
