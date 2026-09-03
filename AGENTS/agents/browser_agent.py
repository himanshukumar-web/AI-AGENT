"""
JARVIS AI — Specialized Browser Agent
Handles controlled browser navigation, Google queries, and page content inspection.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.TOOLS.tool_registry import tool_registry


class BrowserAgent(BaseAgent):
    """Specialized agent for web browsing and page interactions."""

    def __init__(self):
        super().__init__(
            name="browser",
            description="Controls browser navigation, URL launching, search queries, and webpage content extraction.",
            capabilities=["browser_open", "browser_search", "web_navigation", "page_inspection"],
            allowed_tools=["browser.open", "browser.search", "web.open", "web.extract"],
            risk_level="LOW",
            max_steps=5,
            timeout=30.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Execute browser action."""
        action = context.get_input("action", "open")
        url = context.get_input("url", "")
        query = context.get_input("query", context.user_request)

        can_step, reason = context.budget_tracker.can_execute_step()
        if not can_step:
            return AgentResult.fail(reason)

        context.budget_tracker.record_step()

        try:
            if action in ["open", "browser.open", "web.open"] or url:
                target_url = url or query
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool("browser.open", {"url": target_url}, user_request=context.user_request)
                if res.get("success"):
                    return AgentResult.ok(
                        output=f"Opened {target_url} in browser.",
                        metadata=res.get("data", {}),
                        verification_required=True,
                        verification_criteria={"type": "browser", "url": target_url},
                    )
                return AgentResult.fail(res.get("error", "Failed to open URL"))

            if action in ["search", "browser.search"]:
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool("browser.search", {"query": query}, user_request=context.user_request)
                if res.get("success"):
                    return AgentResult.ok(output=f"Searched Google for '{query}'.", metadata=res.get("data", {}))
                return AgentResult.fail(res.get("error", "Browser search failed"))

            if action in ["extract", "web.extract"]:
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool("web.extract", {"url": url}, user_request=context.user_request)
                if res.get("success"):
                    return AgentResult.ok(output=res.get("data", {}))
                return AgentResult.fail(res.get("error", "Web extraction failed"))

            return AgentResult.fail(f"Unsupported browser action: {action}")
        except Exception as e:
            return AgentResult.fail(f"Browser agent error: {e}")
