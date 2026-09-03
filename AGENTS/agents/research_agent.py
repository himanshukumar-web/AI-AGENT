"""
JARVIS AI — Specialized Research Agent
Performs autonomous multi-source web intelligence, claim cross-checking, and report synthesis.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from WEB.research.planner import research_planner, ResearchMode
from WEB.search.provider_manager import search_provider_manager
from WEB.intelligence.comparator import comparison_engine


class ResearchAgent(BaseAgent):
    """Specialized agent for web intelligence and deep research."""

    def __init__(self):
        super().__init__(
            name="research",
            description="Performs multi-source web search, claim cross-checking, comparisons, and verified research reports.",
            capabilities=["web_search", "deep_research", "source_collection", "fact_checking", "comparison", "citations"],
            allowed_tools=[
                "web.search", "web.extract", "web.find", "web.collect_sources",
                "web.compare_sources", "web.research", "web.citations", "research.deep_search"
            ],
            risk_level="LOW",
            max_steps=5,
            timeout=90.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Execute research subtask."""
        action = context.get_input("action", "research")
        query = context.get_input("query", context.user_request)

        can_step, reason = context.budget_tracker.can_execute_step()
        if not can_step:
            return AgentResult.fail(reason)

        context.budget_tracker.record_step()

        try:
            # 1. Comparative Analysis
            if action == "compare" or "compare" in query.lower():
                entities = context.get_input("entities", [])
                if not entities:
                    # Extract entities from query
                    parts = query.replace("compare", "").replace("for my jarvis project", "").replace("for jarvis", "").split("and")
                    if len(parts) == 1 and "," in parts[0]:
                        entities = [e.strip() for e in parts[0].split(",")]
                    else:
                        entities = [p.strip() for p in parts if p.strip()]

                res = comparison_engine.compare(entities)
                output = f"{res.recommendation}\n\n{res.markdown_table}"
                return AgentResult.ok(
                    output=output,
                    metadata={"entities": res.entities, "type": "comparison"},
                    verification_required=True,
                    verification_criteria={"type": "research", "must_contain": "recommendation"},
                )

            # 2. Fast Search
            if action == "search":
                context.budget_tracker.record_tool_call()
                results = search_provider_manager.search(query, max_results=5)
                snippets = [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
                return AgentResult.ok(
                    output=snippets,
                    metadata={"count": len(snippets)},
                    verification_required=True,
                    verification_criteria={"type": "search", "min_results": 1},
                )

            # 3. Deep or Standard Research
            mode_str = context.get_input("mode", "standard").lower()
            mode = ResearchMode.DEEP if mode_str == "deep" else (ResearchMode.QUICK if mode_str == "quick" else ResearchMode.STANDARD)

            context.budget_tracker.record_tool_call()
            res = research_planner.plan_and_execute(query, mode=mode)
            if res.cancelled:
                return AgentResult.fail("Research was cancelled.")

            output = {
                "session_id": res.session_id,
                "summary": res.summary,
                "key_findings": res.key_findings,
                "sources": [s.to_dict() for s in res.sources],
                "full_report": res.full_report,
            }

            return AgentResult.ok(
                output=output,
                artifacts=[{"type": "research_report", "content": res.full_report}],
                metadata={"sources_count": len(res.sources), "mode": mode.value},
                verification_required=True,
                verification_criteria={"type": "research", "min_sources": 1},
            )
        except Exception as e:
            return AgentResult.fail(f"Research execution failed: {e}")
