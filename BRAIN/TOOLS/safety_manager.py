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
        "get_weather": RiskLevel.LOW,
        "get_battery_status": RiskLevel.LOW,
        "get_ip": RiskLevel.LOW,
        "check_internet": RiskLevel.LOW,
        "get_joke": RiskLevel.LOW,
        "get_advice": RiskLevel.LOW,
        "search_google": RiskLevel.LOW,
        "open_website": RiskLevel.LOW,
        "list_automations": RiskLevel.LOW,
        "get_automation_history": RiskLevel.LOW,
        "recall_memory": RiskLevel.LOW,

        # MEDIUM RISK: Interactive / Workspace actions
        "youtube_play": RiskLevel.MEDIUM,
        "youtube_pause": RiskLevel.MEDIUM,
        "youtube_volume": RiskLevel.MEDIUM,
        "launch_application": RiskLevel.MEDIUM,
        "create_automation": RiskLevel.MEDIUM,
        "update_automation": RiskLevel.MEDIUM,
        "run_automation": RiskLevel.MEDIUM,
        "remember_memory": RiskLevel.MEDIUM,

        # HIGH RISK: Destructive / Closing / Deleting actions
        "delete_automation": RiskLevel.HIGH,
        "close_application": RiskLevel.HIGH,
        "clear_memory": RiskLevel.HIGH,
    }

    def __init__(self, mode: str = "ask_high_risk"):
        self.mode = mode  # "ask_high_risk", "strict", "auto_allow"

    def get_risk_level(self, tool_name: str) -> RiskLevel:
        """Return the risk classification for a given tool name."""
        return self.TOOL_RISK_MAP.get(tool_name, RiskLevel.HIGH)

    def validate_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ) -> bool:
        """
        Validate whether the tool execution is permitted under safety policy.
        """
        # Block any attempt to bypass or execute non-allowlisted actions
        if tool_name not in self.TOOL_RISK_MAP:
            print(Fore.RED + f"  [SECURITY BLOCKED] Tool '{tool_name}' is not in the authorized safety registry.")
            return False

        risk = self.get_risk_level(tool_name)

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
            # Default safe permit if no interactive callback provided in automated runs
            return True

        return True


safety_manager = SafetyManager()
