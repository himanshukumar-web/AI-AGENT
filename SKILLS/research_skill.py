"""
JARVIS AI — Research & Web Intelligence Skill Module
Encapsulates deep web research, source extraction, cross-referencing, citations, and action audits.
"""

from typing import Any, Dict, List
from BRAIN.TOOLS.action_logger import action_logger
from SKILLS.base_skill import BaseSkill, SkillCategory


class ResearchSkill(BaseSkill):
    """Provides autonomous deep research, multi-provider web lookup, citations, and action auditing."""

    def __init__(self):
        super().__init__(
            name="research",
            description="Performs autonomous multi-step web research, source cross-checking, and report synthesis.",
            category=SkillCategory.RESEARCH,
        )

    def initialize(self):
        # 1. Deep Research
        def _deep_search(query: str) -> Dict[str, Any]:
            try:
                from WEB.research.planner import research_planner, ResearchMode
                res = research_planner.plan_and_execute(query, mode=ResearchMode.DEEP)
                return {
                    "success": not res.cancelled,
                    "data": {
                        "query": query,
                        "summary": res.summary,
                        "key_findings": res.key_findings,
                        "sources_count": len(res.sources),
                        "full_report": res.full_report,
                    },
                    "error": None,
                }
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="research.deep_search",
            description="Perform autonomous multi-source deep research and report synthesis on a topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic or inquiry to research."}
                },
                "required": ["query"],
            },
            handler=_deep_search,
            risk_level="low",
            aliases=["deep_search", "web.research"],
        )

        # 2. Fast Web Search
        def _web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
            try:
                from WEB.search.provider_manager import search_provider_manager
                results = search_provider_manager.search(query, max_results=max_results)
                return {
                    "success": True,
                    "data": {"query": query, "count": len(results), "results": [r.to_dict() for r in results]},
                    "error": None,
                }
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="web.search",
            description="Execute fast web search across independent search providers.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "max_results": {"type": "integer", "description": "Max results to return."}
                },
                "required": ["query"],
            },
            handler=_web_search,
            risk_level="low",
            aliases=["search", "web_search"],
        )

        # 3. Web Extraction
        def _web_extract(url: str) -> Dict[str, Any]:
            try:
                from WEB.extraction.extractor import web_extractor
                ext = web_extractor.fetch_and_extract(url)
                return {
                    "success": ext.success,
                    "data": {
                        "url": ext.url,
                        "title": ext.title,
                        "text": ext.text,
                        "headings": ext.headings,
                        "tables": ext.tables,
                        "word_count": ext.word_count,
                    },
                    "error": ext.error,
                }
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="web.extract",
            description="Safely extract clean text, headings, and tables from any URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to extract content from."}
                },
                "required": ["url"],
            },
            handler=_web_extract,
            risk_level="low",
            aliases=["extract_webpage"],
        )

        # 4. Comparative Analysis
        def _compare_sources(entities: List[str]) -> Dict[str, Any]:
            try:
                from WEB.intelligence.comparator import comparison_engine
                res = comparison_engine.compare(entities)
                return {
                    "success": True,
                    "data": {
                        "entities": res.entities,
                        "matrix": res.matrix,
                        "markdown_table": res.markdown_table,
                        "recommendation": res.recommendation,
                    },
                    "error": None,
                }
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="web.compare_sources",
            description="Compare multiple frameworks, products, or models in a structured matrix.",
            parameters={
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of names or entities to compare."
                    }
                },
                "required": ["entities"],
            },
            handler=_compare_sources,
            risk_level="low",
            aliases=["compare_entities"],
        )

        # 5. Citations
        def _get_citations() -> Dict[str, Any]:
            try:
                from WEB.intelligence.citations import citation_manager
                cits = [c.__dict__ for c in citation_manager.list_citations()]
                return {
                    "success": True,
                    "data": {"count": len(cits), "citations": cits, "formatted": citation_manager.format_sources_section()},
                    "error": None,
                }
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="web.citations",
            description="Retrieve verified reference citations for active research.",
            parameters={"type": "object", "properties": {}},
            handler=_get_citations,
            risk_level="low",
            aliases=["get_citations"],
        )

        # 6. Action History
        def _get_action_history(limit: int = 10) -> Dict[str, Any]:
            try:
                actions = action_logger.get_recent_actions(limit=limit)
                return {"success": True, "data": {"count": len(actions), "actions": actions}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="action.history",
            description="View recent tool executions and audit records.",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of recent records to retrieve."}
                }
            },
            handler=_get_action_history,
            risk_level="low",
            aliases=["get_recent_actions", "show_recent_actions", "action.audit"],
        )
