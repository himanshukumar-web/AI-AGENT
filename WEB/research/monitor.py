"""
JARVIS AI — Source Monitoring & Update Detection
Detects factual changes between previous research findings and current live sources.
"""

from typing import Any, Dict, List, Optional
from WEB.research.memory import research_memory
from WEB.search.provider_manager import search_provider_manager
from WEB.intelligence.fact_extractor import fact_extractor


class SourceMonitor:
    """Monitors previously researched topics for updates or changes."""

    def check_for_changes(
        self,
        topic_or_query: Optional[str] = None,
        max_fresh_sources: int = 3
    ) -> Dict[str, Any]:
        """
        Compare prior saved research findings against fresh search results.
        Reports whether factual changes or newer versions have been detected.
        """
        # Retrieve baseline research session
        last_session = None
        if topic_or_query:
            results = research_memory.search_saved_research(topic_or_query)
            if results:
                last_session = results[0]

        if not last_session:
            last_session = research_memory.get_last_session()

        if not last_session:
            return {
                "changed": False,
                "summary": "No previous research session found in memory to compare against.",
                "diffs": [],
            }

        target_query = last_session.get("query") or topic_or_query or "Topic"
        prior_findings = last_session.get("findings", [])
        prior_summary = last_session.get("summary", "")

        # Fetch fresh current sources
        fresh_sources = search_provider_manager.search(target_query, max_results=max_fresh_sources)
        if not fresh_sources:
            return {
                "changed": False,
                "summary": f"Could not retrieve fresh live sources to verify '{target_query}'.",
                "diffs": [],
            }

        # Extract fresh claims
        fresh_claims = fact_extractor.extract_claims(fresh_sources, topic=target_query)
        fresh_statements = [c.statement for c in fresh_claims]

        diffs: List[str] = []
        for fresh_stmt in fresh_statements:
            # Check if this statement introduces new facts not present in prior summary/findings
            is_new = True
            fresh_words = set(w.lower() for w in fresh_stmt.split() if len(w) > 3)
            for prior in prior_findings + [prior_summary]:
                prior_words = set(w.lower() for w in prior.split() if len(w) > 3)
                overlap = len(fresh_words.intersection(prior_words))
                if len(fresh_words) > 0 and (float(overlap) / float(len(fresh_words))) > 0.65:
                    is_new = False
                    break

            if is_new and len(fresh_stmt) > 30:
                diffs.append(fresh_stmt)

        changed = len(diffs) > 0
        if changed:
            summary = (
                f"Updates detected for '{target_query}' compared to research from "
                f"{last_session.get('created_at', 'previously')[:10]}:\n" +
                "\n".join(f"- New Information: {d}" for d in diffs[:3])
            )
        else:
            summary = (
                f"Information for '{target_query}' remains consistent with your previous research from "
                f"{last_session.get('created_at', 'previously')[:10]}. No conflicting updates detected."
            )

        return {
            "changed": changed,
            "topic": target_query,
            "session_id": last_session.get("session_id"),
            "summary": summary,
            "diffs": diffs,
        }


# Global singleton instance
source_monitor = SourceMonitor()
