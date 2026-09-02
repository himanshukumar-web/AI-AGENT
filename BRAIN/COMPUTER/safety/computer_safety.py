"""
JARVIS AI — Computer Safety Layer & Action Limits
Enforces risk tiers, per-task action budgets, confirmation gating,
and emergency stop verification.
"""

from enum import Enum
import time
from typing import Any, Dict, Optional, Tuple

from BRAIN.UTILS.logger import jarvis_logger
from BRAIN.COMPUTER.safety.emergency_stop import emergency_stop_controller
from BRAIN.COMPUTER.safety.sensitive_detector import sensitive_detector

# Default Safety Limits
DEFAULT_MAX_ACTIONS = 20
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_DURATION = 60.0  # seconds
DEFAULT_MAX_SCREENSHOTS = 10


class ComputerRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ComputerSafetyManager:
    """Enforces safety constraints, risk tier policies, and action limits."""

    def __init__(
        self,
        max_actions: int = DEFAULT_MAX_ACTIONS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_duration: float = DEFAULT_MAX_DURATION,
        max_screenshots: int = DEFAULT_MAX_SCREENSHOTS,
    ):
        self.max_actions = max_actions
        self.max_retries = max_retries
        self.max_duration = max_duration
        self.max_screenshots = max_screenshots

        # Current task budget state
        self._current_task_id: Optional[str] = None
        self._action_count: int = 0
        self._screenshot_count: int = 0
        self._retry_count: int = 0
        self._task_start_time: float = 0.0

    def start_task(self, task_id: str):
        """Initialize safety budget for a computer control task."""
        self._current_task_id = task_id
        self._action_count = 0
        self._screenshot_count = 0
        self._retry_count = 0
        self._task_start_time = time.time()
        emergency_stop_controller.reset()

    def end_task(self):
        """Reset budget counters after task completes or aborts."""
        self._current_task_id = None
        self._action_count = 0
        self._screenshot_count = 0
        self._retry_count = 0
        self._task_start_time = 0.0

    def classify_action(self, action_name: str, arguments: Optional[Dict[str, Any]] = None) -> ComputerRiskLevel:
        """Categorize computer action into LOW, MEDIUM, or HIGH risk."""
        act = action_name.lower().strip()
        args = arguments or {}

        # 1. High-risk indicators
        high_risk_actions = {
            "computer.delete_file",
            "computer.purchase",
            "computer.submit_form",
            "computer.send_message",
            "computer.modify_security",
            "computer.close_window",
        }
        if act in high_risk_actions:
            return ComputerRiskLevel.HIGH

        # Check for submit/send button clicks
        if act in ("computer.click", "click"):
            target_el = str(args.get("element", "")).lower()
            query = str(args.get("query", "")).lower()
            for trigger in ("submit", "pay", "buy", "checkout", "send", "delete", "confirm payment", "transfer"):
                if trigger in target_el or trigger in query:
                    return ComputerRiskLevel.HIGH

        # Check for typing into sensitive fields
        if act in ("computer.type", "type_text"):
            text = str(args.get("text", ""))
            is_sens, _ = sensitive_detector.is_sensitive_text(text)
            if is_sens:
                return ComputerRiskLevel.HIGH

        # 2. Low-risk actions (read-only perception)
        low_risk_actions = {
            "computer.screenshot",
            "computer.get_screen_size",
            "computer.get_active_window",
            "computer.list_windows",
            "computer.find_element",
            "computer.analyze_screen",
            "computer.scroll",
            "computer.emergency_stop",
        }
        if act in low_risk_actions:
            return ComputerRiskLevel.LOW

        # 3. Medium risk (standard navigation and input)
        return ComputerRiskLevel.MEDIUM

    def check_pre_action_safety(
        self,
        action_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Comprehensive pre-action safety check:
        1. Check emergency stop
        2. Check task budget limits
        3. Check sensitive UI context
        4. Request confirmation for High-risk operations
        """
        # 1. Emergency stop
        if emergency_stop_controller.is_stopped():
            return False, "Action aborted: Emergency stop is active."

        # 2. Check duration limit
        if self._task_start_time > 0:
            elapsed = time.time() - self._task_start_time
            if elapsed > self.max_duration:
                return False, f"Action limit reached: Task exceeded max duration of {self.max_duration}s."

        # 3. Check action count limit
        if self._action_count >= self.max_actions:
            return False, f"Action limit reached: Task reached maximum limit of {self.max_actions} actions."

        # 4. Check risk tier & confirmation
        risk = self.classify_action(action_name, arguments)
        if risk == ComputerRiskLevel.HIGH:
            try:
                from BRAIN.TOOLS.confirmation_center import confirmation_center
                desc = f"Execute high-impact action '{action_name}'"
                if arguments:
                    sanitized_args = {
                        k: sensitive_detector.redact_sensitive_text(str(v))
                        for k, v in arguments.items()
                    }
                    desc += f" with parameters {sanitized_args}"
                confirmed = confirmation_center.request_confirmation(action_name, desc)
                if not confirmed:
                    return False, f"Action '{action_name}' rejected: User did not confirm high-risk action."
            except Exception as e:
                jarvis_logger.warning("SAFETY", f"Confirmation center check bypassed ({e})")

        # Increment action budget
        self._action_count += 1
        return True, ""

    def record_screenshot(self) -> Tuple[bool, str]:
        """Track screenshot budget."""
        if emergency_stop_controller.is_stopped():
            return False, "Emergency stop active."
        if self._screenshot_count >= self.max_screenshots:
            return False, f"Screenshot limit reached ({self.max_screenshots} captures allowed per task)."
        self._screenshot_count += 1
        return True, ""

    def record_retry(self) -> Tuple[bool, str]:
        """Track retry budget."""
        if self._retry_count >= self.max_retries:
            return False, f"Max retries reached ({self.max_retries} attempts allowed per task)."
        self._retry_count += 1
        return True, ""


computer_safety_manager = ComputerSafetyManager()
