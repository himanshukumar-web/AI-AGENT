"""
JARVIS AI — Permission Gate & Safety Policy
Enforces role-based permissions, tool whitelists, and confirmation requirements.
Agents cannot dynamically grant themselves permissions or bypass safety checks.
"""

from enum import Enum
from typing import Any, Dict, Optional, Tuple
from colorama import Fore


class AgentRiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionGate:
    """Enforces execution boundaries and human confirmation for agent actions."""

    def __init__(self):
        # Tools classified as HIGH or CRITICAL risk requiring human approval
        self.CONFIRMATION_REQUIRED_ACTIONS = {
            "system.delete_file": AgentRiskLevel.HIGH,
            "computer.purchase": AgentRiskLevel.CRITICAL,
            "system.modify_security": AgentRiskLevel.CRITICAL,
            "system.shutdown": AgentRiskLevel.HIGH,
            "automation.delete": AgentRiskLevel.HIGH,
        }

    def check_tool_permission(
        self,
        agent_name: str,
        allowed_tools: list,
        tool_name: str,
    ) -> Tuple[bool, str]:
        """Verify the tool is in the agent's explicit allowed_tools whitelist."""
        t_clean = tool_name.lower().strip()
        is_allowed = any(t.lower() == t_clean for t in allowed_tools)
        if not is_allowed:
            return False, f"Permission Denied: Agent '{agent_name}' is not authorized to execute tool '{tool_name}'."
        return True, ""

    def evaluate_action_risk(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Tuple[AgentRiskLevel, bool]:
        """
        Determine risk level and whether human confirmation is mandatory.
        Returns: (risk_level, confirmation_required)
        """
        t_clean = tool_name.lower().strip()

        # Check explicit high/critical mapping
        if t_clean in self.CONFIRMATION_REQUIRED_ACTIONS:
            lvl = self.CONFIRMATION_REQUIRED_ACTIONS[t_clean]
            return lvl, True

        # Check system safety manager risk
        try:
            from BRAIN.TOOLS.safety_manager import safety_manager, RiskLevel
            sm_risk = safety_manager.get_risk_level(t_clean)
            if sm_risk == RiskLevel.HIGH:
                return AgentRiskLevel.HIGH, True
            elif sm_risk == RiskLevel.MEDIUM:
                return AgentRiskLevel.MEDIUM, False
            return AgentRiskLevel.LOW, False
        except Exception:
            return AgentRiskLevel.LOW, False

    def request_approval(
        self,
        agent_name: str,
        action_name: str,
        details: str,
        risk_level: AgentRiskLevel,
    ) -> bool:
        """Prompt user through confirmation center if action is HIGH or CRITICAL."""
        try:
            from BRAIN.CORE_AGENT.confirmation_center import confirmation_center
            prompt_text = (
                f"\n[ACTION APPROVAL REQUIRED]\n"
                f"Agent: {agent_name}\n"
                f"Action: {action_name}\n"
                f"Details: {details}\n"
                f"Risk Level: {risk_level.value}\n"
                f"Do you approve this action? (yes/no): "
            )
            return confirmation_center.request_confirmation(
                action_name=action_name,
                details=details,
                risk_level=risk_level.value.lower(),
            )
        except Exception:
            return False


# Global singleton instance
permission_gate = PermissionGate()
