"""
JARVIS AI — Specialized Memory Agent
Manages user preferences, episodic memories, factual knowledge, and context retrieval.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.TOOLS.tool_registry import tool_registry


class MemoryAgent(BaseAgent):
    """Specialized agent for long-term memory operations and context retrieval."""

    def __init__(self):
        super().__init__(
            name="memory",
            description="Stores preferences, retrieves episodic context, and queries long-term semantic memory.",
            capabilities=["memory_store", "memory_recall", "memory_search", "memory_forget", "context_selection"],
            allowed_tools=["memory.remember", "memory.recall", "memory.forget", "memory.search", "memory.list"],
            risk_level="LOW",
            max_steps=3,
            timeout=20.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Execute memory subtask."""
        action = context.get_input("action", "recall")
        params = context.get_input("params", {})

        can_step, reason = context.budget_tracker.can_execute_step()
        if not can_step:
            return AgentResult.fail(reason)

        context.budget_tracker.record_step()

        try:
            # 1. Store preference / fact
            if action in ["store", "remember", "memory.remember"]:
                key = params.get("key") or context.get_input("key", "user_note")
                value = params.get("value") or context.get_input("value", context.user_request)
                category = params.get("category", "preference")
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool(
                    "memory.remember",
                    {"key": key, "value": value, "category": category},
                    user_request=context.user_request,
                )
                if res.get("success"):
                    return AgentResult.ok(
                        output=f"Stored in memory: {key} = {value}",
                        metadata={"key": key},
                        verification_required=True,
                        verification_criteria={"type": "memory", "key": key},
                    )
                return AgentResult.fail(res.get("error", "Memory store failed"))

            # 2. Recall memory
            if action in ["recall", "memory.recall"]:
                query = params.get("query") or context.get_input("query", None)
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool("memory.recall", {"query": query} if query else {}, user_request=context.user_request)
                if res.get("success"):
                    facts = res.get("data", {}).get("facts", [])
                    return AgentResult.ok(output=facts, metadata={"count": len(facts)})
                return AgentResult.fail(res.get("error", "Memory recall failed"))

            # 3. Forget memory
            if action in ["forget", "memory.forget"]:
                key = params.get("key") or context.get_input("key", "")
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool("memory.forget", {"key": key}, user_request=context.user_request)
                if res.get("success"):
                    return AgentResult.ok(output=f"Forgot memory: {key}")
                return AgentResult.fail(res.get("error", "Memory forget failed"))

            return AgentResult.fail(f"Unsupported memory action: {action}")
        except Exception as e:
            return AgentResult.fail(f"Memory agent error: {e}")
