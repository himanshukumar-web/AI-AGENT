"""
JARVIS AI — Structured Research Report Generator
Generates clean, standardized, cited markdown reports for deep research inquiries.
"""

from typing import Any, Dict, List, Optional
from WEB.intelligence.citations import Citation
from WEB.intelligence.cross_checker import CrossCheckResult
from WEB.intelligence.fact_extractor import ExtractedClaim


class ResearchReportGenerator:
    """Formats research findings into executive-grade structured reports."""

    def generate_report(
        self,
        title: str,
        query: str,
        summary: str,
        key_findings: List[str],
        evidence_claims: List[ExtractedClaim],
        cross_check_result: Optional[CrossCheckResult] = None,
        comparison_table: Optional[str] = None,
        recommendation: Optional[str] = None,
        citations: Optional[List[Citation]] = None,
    ) -> str:
        """Construct full structured markdown report according to JARVIS Phase 14 specifications."""
        sections = []

        # Header
        sections.append(f"# Research Report: {title}\n*Topic Inquiry:* {query}")

        # 1. Executive Summary
        sections.append(f"## Executive Summary\n{summary}")

        # 2. Key Findings
        if key_findings:
            findings_md = "\n".join(f"- {f}" for f in key_findings)
            sections.append(f"## Key Findings\n{findings_md}")

        # 3. Evidence & Grounded Claims
        if evidence_claims:
            ev_lines = []
            for c in evidence_claims:
                urls_str = " ".join(f"[{u}]" for u in c.source_urls) if c.source_urls else ""
                conf_badge = f"**[{c.confidence} Confidence]**"
                ev_lines.append(f"- {conf_badge} {c.statement}")
            sections.append(f"## Evidence\n" + "\n".join(ev_lines))

        # 4. Comparison (if applicable)
        if comparison_table:
            sections.append(f"## Comparative Analysis\n{comparison_table}")

        # 5. Conflicting Information (if detected)
        if cross_check_result and cross_check_result.conflicting_claims:
            conflict_lines = []
            for conf in cross_check_result.conflicting_claims:
                conflict_lines.append(f"- **{conf['entity']}:** {conf['explanation']}")
            sections.append(f"## Conflicting Information\n" + "\n".join(conflict_lines))

        # 6. Recommendation (if appropriate)
        if recommendation:
            sections.append(f"## Recommendation\n{recommendation}")

        # 7. Sources & References
        if citations:
            cit_lines = []
            for c in citations:
                cit_lines.append(f"[{c.index}] **{c.title}** — {c.domain}  \n    <{c.url}>")
            sections.append(f"## Sources\n" + "\n\n".join(cit_lines))

        return "\n\n---\n\n".join(sections)


# Global singleton instance
research_report_generator = ResearchReportGenerator()
