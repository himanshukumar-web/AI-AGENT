"""
JARVIS AI — Specialized System Agent
Executes safe system-level utilities (time, battery, diagnostics, weather, app launching).
Arbitrary shell execution is strictly prohibited.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.TOOLS.tool_registry import tool_registry


class SystemAgent(BaseAgent):
    """Specialized agent for safe system-level tasks and telemetry."""

    def __init__(self):
        super().__init__(
            name="system",
            description="Manages system telemetry (time, battery, IP, internet, diagnostics) and safe application launching.",
            capabilities=["system_time", "system_battery", "system_ip", "system_internet", "system_diagnostics", "launch_application", "weather"],
            allowed_tools=[
                "system.time", "system.battery", "system.ip", "system.internet",
                "system.diagnostics", "system.launch_app", "system.joke",
                "system.advice", "weather.get"
            ],
            risk_level="LOW",
            max_steps=3,
            timeout=20.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Execute system utility subtask."""
        action = context.get_input("action", "time")
        params = context.get_input("params", {})

        can_step, reason = context.budget_tracker.can_execute_step()
        if not can_step:
            return AgentResult.fail(reason)

        context.budget_tracker.record_step()

        try:
            # Map action to tool name
            if action in ["time", "get_time"]:
                tool_name = "system.time"
            elif action in ["battery", "get_battery"]:
                tool_name = "system.battery"
            elif action in ["ip", "get_ip"]:
                tool_name = "system.ip"
            elif action in ["internet", "check_internet"]:
                tool_name = "system.internet"
            elif action in ["diagnostics", "doctor"]:
                tool_name = "system.diagnostics"
            elif action in ["weather"]:
                tool_name = "weather.get"
            elif action in ["launch_app", "open_app"]:
                tool_name = "system.launch_app"
            else:
                tool_name = action if action.startswith("system.") or action.startswith("weather.") else f"system.{action}"

            if not self.is_tool_allowed(tool_name):
                return AgentResult.fail(f"Tool '{tool_name}' is not authorized for SystemAgent.")

            context.budget_tracker.record_tool_call()
            res = tool_registry.execute_tool(tool_name, params, user_request=context.user_request)

            if res.get("success"):
                return AgentResult.ok(output=res.get("data", {}), metadata={"tool": tool_name})
            return AgentResult.fail(res.get("error", f"Tool execution failed for {tool_name}"))
        except Exception as e:
            return AgentResult.fail(f"System agent error: {e}")
