"""
JARVIS AI — Research Cancellation Controller
Provides thread-safe cancellation tokens for gracefully terminating active research tasks.
"""

import threading


class ResearchCancellationToken:
    """Thread-safe cooperative cancellation coordinator."""

    def __init__(self):
        self._stop_event = threading.Event()

    def request_cancellation(self, reason: str = "User requested research cancellation"):
        """Trigger cancellation."""
        self._stop_event.set()
        # Also signal the research planner singleton
        try:
            from WEB.research.planner import research_planner
            research_planner.request_cancellation()
        except Exception:
            pass

    def is_cancelled(self) -> bool:
        """Check whether cancellation was signaled."""
        return self._stop_event.is_set()

    def reset(self):
        """Clear cancellation state for next operation."""
        self._stop_event.clear()
        try:
            from WEB.research.planner import research_planner
            research_planner.reset_cancellation()
        except Exception:
            pass


# Global singleton instance
research_cancellation = ResearchCancellationToken()
