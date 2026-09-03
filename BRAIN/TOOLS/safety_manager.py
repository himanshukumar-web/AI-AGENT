"""
JARVIS AI — Safety & Action Confirmation Manager
Enforces strict security bounds, action risk levels, and confirmation checks.
Arbitrary shell/code execution is strictly prohibited.
"""

from enum import Enum
from typing import Any, Callable, Dict, Optional
from colorama import Fore


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyManager:
    """Evaluates and validates tool action permissions and confirmations."""

    TOOL_RISK_MAP = {
        # LOW RISK: Informational / Read-only / Safe operations
        "get_time": RiskLevel.LOW,
        "system.time": RiskLevel.LOW,
        "get_weather": RiskLevel.LOW,
        "weather.get": RiskLevel.LOW,
        "get_battery_status": RiskLevel.LOW,
        "system.battery": RiskLevel.LOW,
        "get_ip": RiskLevel.LOW,
        "system.ip": RiskLevel.LOW,
        "check_internet": RiskLevel.LOW,
        "system.internet": RiskLevel.LOW,
        "get_joke": RiskLevel.LOW,
        "system.joke": RiskLevel.LOW,
        "get_advice": RiskLevel.LOW,
        "system.advice": RiskLevel.LOW,
        "search_google": RiskLevel.LOW,
        "browser.search": RiskLevel.LOW,
        "open_website": RiskLevel.LOW,
        "browser.open": RiskLevel.LOW,
        "list_automations": RiskLevel.LOW,
        "automation.list": RiskLevel.LOW,
        "get_automation_history": RiskLevel.LOW,
        "automation.history": RiskLevel.LOW,
        "recall_memory": RiskLevel.LOW,
        "memory.recall": RiskLevel.LOW,
        "memory.list": RiskLevel.LOW,
        "research.deep_search": RiskLevel.LOW,
        "deep_search": RiskLevel.LOW,
        "web.search": RiskLevel.LOW,
        "web.research": RiskLevel.LOW,
        "web.extract": RiskLevel.LOW,
        "web.find": RiskLevel.LOW,
        "web.collect_sources": RiskLevel.LOW,
        "web.compare_sources": RiskLevel.LOW,
        "web.citations": RiskLevel.LOW,
        "web.open": RiskLevel.LOW,
        "system.diagnostics": RiskLevel.LOW,
        "doctor": RiskLevel.LOW,
        "run_diagnostics": RiskLevel.LOW,
        "system.health": RiskLevel.LOW,
        "action.history": RiskLevel.LOW,
        "get_recent_actions": RiskLevel.LOW,
        "show_recent_actions": RiskLevel.LOW,
        "action.audit": RiskLevel.LOW,
        "memory.save": RiskLevel.MEDIUM,
        "memory.search": RiskLevel.LOW,

        # COMPUTER USE: LOW RISK (Read-only / Observation)
        "computer.screenshot": RiskLevel.LOW,
        "computer.get_screen_size": RiskLevel.LOW,
        "computer.get_active_window": RiskLevel.LOW,
        "computer.list_windows": RiskLevel.LOW,
        "computer.find_element": RiskLevel.LOW,
        "computer.analyze_screen": RiskLevel.LOW,
        "computer.scroll": RiskLevel.LOW,
        "computer.emergency_stop": RiskLevel.LOW,

        # MEDIUM RISK: Interactive / Workspace actions
        "youtube_play": RiskLevel.MEDIUM,
        "youtube.play": RiskLevel.MEDIUM,
        "youtube.search": RiskLevel.MEDIUM,
        "youtube_pause": RiskLevel.MEDIUM,
        "youtube.pause": RiskLevel.MEDIUM,
        "youtube_volume": RiskLevel.MEDIUM,
        "youtube.volume": RiskLevel.MEDIUM,
        "launch_application": RiskLevel.MEDIUM,
        "system.launch_app": RiskLevel.MEDIUM,
        "create_automation": RiskLevel.MEDIUM,
        "automation.create": RiskLevel.MEDIUM,
        "update_automation": RiskLevel.MEDIUM,
        "automation.update": RiskLevel.MEDIUM,
        "run_automation": RiskLevel.MEDIUM,
        "automation.run": RiskLevel.MEDIUM,
        "remember_memory": RiskLevel.MEDIUM,
        "memory.remember": RiskLevel.MEDIUM,

        # COMPUTER USE: MEDIUM RISK (Interactive Controlled Input)
        "computer.move_mouse": RiskLevel.MEDIUM,
        "computer.click": RiskLevel.MEDIUM,
        "computer.double_click": RiskLevel.MEDIUM,
        "computer.right_click": RiskLevel.MEDIUM,
        "computer.drag": RiskLevel.MEDIUM,
        "computer.type": RiskLevel.MEDIUM,
        "computer.press_key": RiskLevel.MEDIUM,
        "computer.hotkey": RiskLevel.MEDIUM,
        "computer.focus_window": RiskLevel.MEDIUM,

        # HIGH RISK: Destructive / Closing / Deleting actions
        "delete_automation": RiskLevel.HIGH,
        "automation.delete": RiskLevel.HIGH,
        "close_application": RiskLevel.HIGH,
        "system.close_app": RiskLevel.HIGH,
        "clear_memory": RiskLevel.HIGH,
        "memory.forget": RiskLevel.HIGH,
        "computer.close_window": RiskLevel.HIGH,
    }

    def __init__(self, mode: str = "ask_high_risk"):
        self.mode = mode  # "ask_high_risk", "strict", "auto_allow"

    def get_risk_level(self, tool_name: str) -> RiskLevel:
        """Return the risk classification for a given tool name."""
        return self.TOOL_RISK_MAP.get(tool_name.lower().strip(), RiskLevel.HIGH)

    def is_tool_registered(self, tool_name: str) -> bool:
        """Check if tool is in allowlist."""
        return tool_name.lower().strip() in self.TOOL_RISK_MAP

    def validate_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ) -> bool:
        """
        Validate whether the tool execution is permitted under safety policy.
        """
        clean_name = tool_name.lower().strip()
        if not self.is_tool_registered(clean_name):
            print(Fore.RED + f"  [SECURITY BLOCKED] Tool '{tool_name}' is not in the authorized safety registry.")
            return False

        risk = self.get_risk_level(clean_name)

        if self.mode == "auto_allow":
            return True

        if self.mode == "strict" and risk in (RiskLevel.MEDIUM, RiskLevel.HIGH):
            if confirm_callback:
                return confirm_callback(f"Execute {risk.value.upper()} risk tool '{tool_name}' with args {arguments}?")
            return False

        if self.mode == "ask_high_risk" and risk == RiskLevel.HIGH:
            if confirm_callback:
                prompt = f"Confirm HIGH-RISK action: '{tool_name}' with parameters {arguments}? (y/n): "
                return confirm_callback(prompt)
            return True

        return True


safety_manager = SafetyManager()
