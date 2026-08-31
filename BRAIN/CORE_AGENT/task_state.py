"""
JARVIS AI — Task State Machine & Interruption Manager
Maintains execution lifecycle state and enables immediate, safe user interruption (barge-in).
"""

from enum import Enum
import threading
from typing import Optional
from colorama import Fore


class TaskState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    SEARCHING = "searching"
    EXECUTING = "executing"
    WAITING_CONFIRMATION = "waiting_confirmation"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"


class TaskStateManager:
    """Manages active task state and cancellation flags."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = TaskState.IDLE
        self._current_task_name = ""
        self._stop_requested = False

    @property
    def state(self) -> TaskState:
        return self._state

    @property
    def current_task_name(self) -> str:
        return self._current_task_name

    def set_state(self, state: TaskState, task_name: Optional[str] = None):
        """Transition task state."""
        with self._lock:
            self._state = state
            if task_name is not None:
                self._current_task_name = task_name
            if state == TaskState.IDLE or state == TaskState.COMPLETED:
                self._stop_requested = False

    def request_interruption(self) -> bool:
        """User triggered interruption (e.g. 'Jarvis stop', 'Cancel')."""
        with self._lock:
            self._stop_requested = True
            self._state = TaskState.INTERRUPTED
            # Halt audio playback immediately
            try:
                from VOICE.voice_engine import voice_engine
                voice_engine.stop_speaking()
            except Exception:
                pass
            print(Fore.YELLOW + f"  [Interruption] Task '{self._current_task_name}' safely stopped.")
            return True

    def is_interrupted(self) -> bool:
        """Check if interruption was requested."""
        return self._stop_requested

    def reset(self):
        """Reset state to IDLE."""
        with self._lock:
            self._state = TaskState.IDLE
            self._current_task_name = ""
            self._stop_requested = False


# Global singleton instance
task_state_manager = TaskStateManager()
