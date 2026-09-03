"""
JARVIS AI — Research Planner & Autonomous Investigation Engine
Orchestrates intent detection, multi-query expansion, source collection, content extraction,
cross-checking, comparison, grounded synthesis, and verified citations across Quick, Standard, and Deep modes.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Callable, Dict, List, Optional
import uuid

from config import (
    RESEARCH_DEPTH, MAX_SEARCHES, MAX_SOURCES,
    MAX_PAGE_FETCHES, MAX_RESEARCH_TIME
)
from WEB.search.base import SearchResult
from WEB.search.provider_manager import search_provider_manager
from WEB.extraction.extractor import web_extractor
from WEB.extraction.deduplicator import source_deduplicator
from WEB.intelligence.source_scorer import source_scorer
from WEB.intelligence.fact_extractor import fact_extractor, ExtractedClaim
from WEB.intelligence.cross_checker import cross_checker, CrossCheckResult
from WEB.intelligence.comparator import comparison_engine
from WEB.intelligence.citations import citation_manager
from WEB.intelligence.recency import recency_analyzer
from WEB.research.report_generator import research_report_generator
from WEB.research.memory import research_memory
from WEB.security.sanitizer import web_sanitizer
from WEB.security.rate_limiter import research_rate_limiter
from WEB.security.cancellation import research_cancellation


class ResearchMode(Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class ResearchSessionResult:
    """The final structured outcome of an autonomous research task."""
    session_id: str
    query: str
    mode: ResearchMode
    summary: str
    key_findings: List[str] = field(default_factory=list)
    sources: List[SearchResult] = field(default_factory=list)
    claims: List[ExtractedClaim] = field(default_factory=list)
    cross_check: Optional[CrossCheckResult] = None
    comparison_table: Optional[str] = None
    full_report: Optional[str] = None
    duration_ms: float = 0.0
    cancelled: bool = False
    rate_limited: bool = False


class ResearchPlanner:
    """Autonomous investigator decomposing and executing multi-step web research."""

    def __init__(self):
        self._cancellation_requested = False

    def request_cancellation(self):
        """Signal ongoing research to halt immediately."""
        self._cancellation_requested = True

    def reset_cancellation(self):
        self._cancellation_requested = False

    def detect_mode(self, text: str) -> ResearchMode:
        """Infer research mode from user prompt or configuration."""
        t = text.lower().strip()
        if any(w in t for w in ["quick", "quickly", "briefly", "short", "fast research"]):
            return ResearchMode.QUICK
        if any(w in t for w in ["deep research", "thorough", "comprehensive", "detailed research", "in-depth"]):
            return ResearchMode.DEEP

        default_mode = RESEARCH_DEPTH.lower()
        if default_mode == "quick":
            return ResearchMode.QUICK
        if default_mode == "deep":
            return ResearchMode.DEEP
        return ResearchMode.STANDARD

    def generate_targeted_queries(self, query: str, mode: ResearchMode) -> List[str]:
        """
        Generate multiple targeted sub-queries to capture comprehensive evidence (Phase 3).
        Avoids redundant search terms while covering benchmarks, docs, and community activity.
        """
        clean_q = query.strip()
        queries = [clean_q]

        if mode == ResearchMode.QUICK:
            return queries

        # Check if comparison
        if "compare" in clean_q.lower() or " vs " in clean_q.lower():
            return queries

        # Targeted facet expansion
        queries.append(f"{clean_q} official documentation")
        queries.append(f"{clean_q} benchmarks comparison")

        if mode == ResearchMode.DEEP:
            queries.append(f"{clean_q} github release notes")
            queries.append(f"{clean_q} community adoption 2026")

        # Cap by MAX_SEARCHES
        return queries[:MAX_SEARCHES]

    def _detect_comparison_entities(self, query: str) -> List[str]:
        """Detect entities to compare if query is a comparison."""
        t = query.lower()
        if "compare" in t or " vs " in t:
            clean = t.replace("compare", "").replace("for my jarvis project", "").strip()
            # Split on 'and', 'vs', ','
            import re
            parts = re.split(r",|\sand\s|\svs\s", clean)
            entities = [p.strip() for p in parts if len(p.strip()) > 1]
            if len(entities) >= 2:
                return entities
        return []

    def plan_and_execute(
        self,
        query: str,
        mode: Optional[ResearchMode] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        provider_name: Optional[str] = None,
    ) -> ResearchSessionResult:
        """
        Main autonomous research execution loop.
        Pipeline: Intent -> Query Gen -> Search -> Dedup -> Extract -> Score -> Fact Extract -> Cross-check -> Synthesize.
        """
        start_time = time.perf_counter()
        self.reset_cancellation()
        research_cancellation.reset()
        research_rate_limiter.start_session()
        session_id = str(uuid.uuid4())[:8]

        actual_mode = mode or self.detect_mode(query)
        citation_manager.reset()
        rate_limited = False

        def _update_status(msg: str):
            if status_callback:
                try:
                    status_callback(msg)
                except Exception:
                    pass

        # ── 1. Check for immediate cancellation ──────────────────────────
        if self._cancellation_requested or research_cancellation.is_cancelled():
            return ResearchSessionResult(
                session_id=session_id, query=query, mode=actual_mode,
                summary="Research was cancelled by user.", cancelled=True
            )

        # ── 2. Comparison Engine Short-circuit ───────────────────────────
        compare_entities = self._detect_comparison_entities(query)
        comparison_res = None
        if compare_entities:
            _update_status("Analyzing comparative profiles...")
            comparison_res = comparison_engine.compare(compare_entities)

        # ── 3. Query Generation ──────────────────────────────────────────
        _update_status("Formulating research strategy and queries...")
        search_queries = self.generate_targeted_queries(query, actual_mode)

        # ── 4. Source Collection ─────────────────────────────────────────
        _update_status("Searching and collecting independent sources...")
        max_res_per_q = 2 if actual_mode == ResearchMode.QUICK else 4
        raw_sources: List[SearchResult] = []
        for q in search_queries:
            if self._cancellation_requested or research_cancellation.is_cancelled():
                return ResearchSessionResult(
                    session_id=session_id, query=query, mode=actual_mode,
                    summary="Research cancelled during source collection.", cancelled=True
                )
            can_search, err = research_rate_limiter.can_search()
            if not can_search:
                rate_limited = True
                _update_status("Search query limit reached. Continuing with collected sources...")
                break

            research_rate_limiter.record_search()
            results = search_provider_manager.search(q, max_results=max_res_per_q, provider_name=provider_name)
            raw_sources.extend(results)

        # ── 5. Deduplication ─────────────────────────────────────────────
        unique_sources = source_deduplicator.deduplicate(raw_sources)
        max_sources_allowed = 3 if actual_mode == ResearchMode.QUICK else MAX_SOURCES
        target_sources = unique_sources[:max_sources_allowed]

        # ── 6. Content Extraction & Source Quality Scoring ───────────────
        _update_status("Reviewing documentation and evaluating source authority...")
        fetch_count = min(len(target_sources), MAX_PAGE_FETCHES if actual_mode == ResearchMode.DEEP else 3)

        for i in range(fetch_count):
            if self._cancellation_requested or research_cancellation.is_cancelled():
                break
            src = target_sources[i]
            # Register in Citation Manager
            citation_manager.register_source(src)

            # Extract deep readable content if URL is valid HTTP and under rate limit
            if src.url.startswith("http") and not src.raw_content:
                can_fetch, _ = research_rate_limiter.can_fetch_page()
                if can_fetch:
                    research_rate_limiter.record_page_fetch()
                    try:
                        ext = web_extractor.fetch_and_extract(src.url)
                        if ext.success and ext.text:
                            # Sanitize extracted untrusted web content to neutralize injection attacks
                            src.raw_content = web_sanitizer.sanitize_web_content(ext.text)
                            if ext.publication_date:
                                src.publication_date = ext.publication_date
                    except Exception:
                        pass
                else:
                    rate_limited = True

            # Score source
            score = source_scorer.score_source(src, query=query, content_text=src.raw_content)
            src.relevance_score = score.overall_score

        # ── 7. Fact Extraction ───────────────────────────────────────────
        _update_status("Extracting verifiable claims and evidence...")
        extracted_claims = fact_extractor.extract_claims(target_sources, topic=query)

        # ── 8. Cross-Checking & Disagreement Detection ───────────────────
        _update_status("Cross-referencing evidence and verifying consistency...")
        cross_check_res = cross_checker.cross_check(extracted_claims)

        # ── 9. Evidence Synthesis ────────────────────────────────────────
        _update_status("Synthesizing final research report with citations...")

        # Build grounded key findings
        key_findings: List[str] = []
        for c in cross_check_res.verified_claims[:5]:
            cit_tag = ""
            if c.source_urls:
                cit_tag = " " + " ".join(citation_manager.get_citation_tag(u) for u in c.source_urls if citation_manager.get_citation_tag(u))
            key_findings.append(f"{c.statement}{cit_tag}")

        if not key_findings:
            for s in target_sources[:3]:
                cit_tag = citation_manager.get_citation_tag(s.url)
                key_findings.append(f"{s.snippet} {cit_tag}".strip())

        # Generate summary
        if comparison_res and comparison_res.recommendation:
            summary = comparison_res.recommendation
        elif key_findings:
            summary = " ".join(key_findings[:2])
        else:
            summary = f"Research concluded for '{query}' across {len(target_sources)} independent sources."

        # ── 10. Report Formatting ────────────────────────────────────────
        full_report = None
        if actual_mode == ResearchMode.DEEP or "report" in query.lower():
            full_report = research_report_generator.generate_report(
                title=query.title(),
                query=query,
                summary=summary,
                key_findings=key_findings,
                evidence_claims=cross_check_res.verified_claims,
                cross_check_result=cross_check_res,
                comparison_table=comparison_res.markdown_table if comparison_res else None,
                recommendation=comparison_res.recommendation if comparison_res else None,
                citations=citation_manager.list_citations(),
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        session_result = ResearchSessionResult(
            session_id=session_id,
            query=query,
            mode=actual_mode,
            summary=summary,
            key_findings=key_findings,
            sources=target_sources,
            claims=cross_check_res.verified_claims,
            cross_check=cross_check_res,
            comparison_table=comparison_res.markdown_table if comparison_res else None,
            full_report=full_report,
            duration_ms=duration_ms,
            cancelled=False,
            rate_limited=rate_limited,
        )

        # Save to memory
        research_memory.save_session(
            session_id=session_id,
            title=query.title(),
            query=query,
            mode=actual_mode.value,
            summary=summary,
            key_findings=key_findings,
            sources=[s.to_dict() for s in target_sources],
            full_report=full_report or summary,
        )

        return session_result


# Global singleton instance
research_planner = ResearchPlanner()
