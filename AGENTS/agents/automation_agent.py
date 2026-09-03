"""
JARVIS AI — Specialized Automation Agent
Handles custom automations, YouTube controls, background schedules, and app workflows.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.TOOLS.tool_registry import tool_registry


class AutomationAgent(BaseAgent):
    """Specialized agent for custom automations and scheduled workflows."""

    def __init__(self):
        super().__init__(
            name="automation",
            description="Manages custom automations, schedules, YouTube interactions, and background tasks.",
            capabilities=["automation_create", "automation_run", "automation_list", "automation_schedule", "youtube_play", "youtube_search"],
            allowed_tools=[
                "automation.create", "automation.run", "automation.list",
                "automation.history", "automation.delete", "youtube.play",
                "youtube.search", "youtube.pause", "youtube.volume"
            ],
            risk_level="MEDIUM",
            max_steps=5,
            timeout=30.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Execute automation subtask."""
        action = context.get_input("action", "run")
        params = context.get_input("params", {})

        can_step, reason = context.budget_tracker.can_execute_step()
        if not can_step:
            return AgentResult.fail(reason)

        context.budget_tracker.record_step()

        try:
            # 1. Create automation
            if action in ["create", "automation.create", "create_automation"]:
                name = params.get("name") or context.get_input("name", "Custom Task")
                action_name = params.get("action_name") or context.get_input("action_name", "speak_text")
                schedule_time = params.get("schedule_time") or context.get_input("schedule_time", "08:00")
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool(
                    "automation.create",
                    {"name": name, "action_name": action_name, "schedule_time": schedule_time},
                    user_request=context.user_request,
                )
                if res.get("success"):
                    return AgentResult.ok(
                        output=f"Created automation '{name}' scheduled for {schedule_time}.",
                        metadata=res.get("data", {}),
                        verification_required=True,
                        verification_criteria={"type": "automation", "name": name},
                    )
                return AgentResult.fail(res.get("error", "Failed to create automation"))

            # 2. List automations
            if action in ["list", "automation.list", "list_automations"]:
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool("automation.list", {}, user_request=context.user_request)
                if res.get("success"):
                    autos = res["data"].get("automations", [])
                    return AgentResult.ok(output=autos, metadata={"count": len(autos)})
                return AgentResult.fail(res.get("error", "Failed to list automations"))

            # 3. YouTube Search / Play
            if "youtube" in action:
                query = params.get("query") or context.get_input("query", "")
                tool_name = "youtube.play" if "play" in action else "youtube.search"
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool(tool_name, {"query": query}, user_request=context.user_request)
                if res.get("success"):
                    return AgentResult.ok(output=res.get("data", {}), metadata={"tool": tool_name})
                return AgentResult.fail(res.get("error", "YouTube action failed"))

            # Default generic automation tool execution
            tool_name = action if action.startswith("automation.") else f"automation.{action}"
            if self.is_tool_allowed(tool_name):
                context.budget_tracker.record_tool_call()
                res = tool_registry.execute_tool(tool_name, params, user_request=context.user_request)
                if res.get("success"):
                    return AgentResult.ok(output=res.get("data", {}))
                return AgentResult.fail(res.get("error", "Tool execution failed"))

            return AgentResult.fail(f"Unsupported automation action: {action}")
        except Exception as e:
            return AgentResult.fail(f"Automation execution error: {e}")
