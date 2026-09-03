"""
JARVIS AI — Specialized Computer Use Agent
Handles desktop perception, UI element localization, bounded mouse/keyboard control, and windows.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.TOOLS.tool_registry import tool_registry


class ComputerAgent(BaseAgent):
    """Specialized agent for visual desktop control and window management."""

    def __init__(self):
        super().__init__(
            name="computer",
            description="Perceives desktop screen, detects UI elements, controls mouse/keyboard with boundaries, and manages windows.",
            capabilities=["screen_perception", "find_element", "mouse_click", "mouse_scroll", "keyboard_type", "window_management", "active_window"],
            allowed_tools=[
                "computer.screenshot", "computer.get_screen_size", "computer.get_active_window",
                "computer.list_windows", "computer.find_element", "computer.analyze_screen",
                "computer.click", "computer.double_click", "computer.right_click",
                "computer.type_text", "computer.press_key", "computer.hotkey",
                "computer.scroll", "computer.focus_window", "computer.emergency_stop"
            ],
            risk_level="MEDIUM",
            max_steps=10,
            timeout=60.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Execute computer control subtask."""
        action = context.get_input("action", "analyze_screen")
        params = context.get_input("params", {})

        can_step, reason = context.budget_tracker.can_execute_step()
        if not can_step:
            return AgentResult.fail(reason)

        context.budget_tracker.record_step()

        try:
            # Map action to canonical tool name
            tool_name = action if action.startswith("computer.") else f"computer.{action}"
            if not self.is_tool_allowed(tool_name):
                return AgentResult.fail(f"Tool '{tool_name}' is not permitted for ComputerAgent.")

            context.budget_tracker.record_tool_call()
            res = tool_registry.execute_tool(tool_name, params, user_request=context.user_request)

            if res.get("success"):
                verification_criteria = None
                if tool_name in ["computer.focus_window", "computer.click"]:
                    verification_criteria = {"type": "window_check"}

                return AgentResult.ok(
                    output=res.get("data", {}),
                    metadata={"tool": tool_name},
                    verification_required=(verification_criteria is not None),
                    verification_criteria=verification_criteria,
                )
            return AgentResult.fail(res.get("error", f"Execution of {tool_name} failed."))
        except Exception as e:
            return AgentResult.fail(f"Computer agent error: {e}")
