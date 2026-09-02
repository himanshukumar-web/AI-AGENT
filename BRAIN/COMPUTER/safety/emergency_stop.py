"""
JARVIS AI — Global Emergency Stop System
Provides immediate, non-blocking abortion of computer control actions
independent of LLM response latency.
"""

import threading
import time
from typing import Optional, List, Callable
from BRAIN.UTILS.logger import jarvis_logger

STOP_PHRASES = {
    "stop",
    "jarvis stop",
    "stop everything",
    "cancel computer task",
    "stop computer",
    "emergency stop",
    "abort",
    "ruko",
    "chup",
    "bas karo",
    "ruk jao",
    "hold on stop",
}


class EmergencyStopController:
    """Thread-safe global emergency stop mechanism."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._stop_reason: str = ""
        self._stop_timestamp: float = 0.0
        self._callbacks: List[Callable[[], None]] = []

    def request_stop(self, reason: str = "User requested emergency stop") -> bool:
        """Immediately triggers the emergency stop flag."""
        self._stop_reason = reason
        self._stop_timestamp = time.time()
        self._stop_event.set()

        jarvis_logger.warning("EMERGENCY_STOP", f"EMERGENCY STOP ACTIVATED: {reason}")

        # Also signal the core task state manager if available
        try:
            from BRAIN.CORE_AGENT.task_state import task_state_manager
            task_state_manager.request_interruption()
        except Exception:
            pass

        # Execute registered abort callbacks
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                pass

        return True

    def is_stopped(self) -> bool:
        """Check if emergency stop is currently active."""
        return self._stop_event.is_set()

    def check_and_raise(self):
        """Raises InterruptedError if emergency stop is active."""
        if self.is_stopped():
            raise InterruptedError(f"Computer control interrupted: {self._stop_reason}")

    def reset(self):
        """Resets the emergency stop state for the next session."""
        self._stop_event.clear()
        self._stop_reason = ""
        self._stop_timestamp = 0.0

    def register_abort_callback(self, callback: Callable[[], None]):
        """Register a callback to run immediately upon emergency stop."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def is_emergency_phrase(self, text: str) -> bool:
        """Determines if a natural language phrase is an emergency stop request."""
        t = text.strip().lower()
        if t in STOP_PHRASES:
            return True
        for phrase in STOP_PHRASES:
            if t == phrase or t.startswith(f"{phrase} ") or t.endswith(f" {phrase}"):
                return True
        return False


emergency_stop_controller = EmergencyStopController()
