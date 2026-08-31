"""
JARVIS AI — Observability & Metrics Tracker
Tracks response latency, LLM invocation counts, tool execution durations, and token usage estimates.
"""

import time
import threading
from typing import Any, Dict, List


class MetricsTracker:
    """Thread-safe metrics accumulator for JARVIS runtime observability."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_llm_calls = 0
        self._total_tool_calls = 0
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._latencies_ms: List[float] = []

    def record_llm_call(self, duration_ms: float, prompt_tokens: int = 0, completion_tokens: int = 0):
        """Record an LLM API call with latency and token metrics."""
        with self._lock:
            self._total_llm_calls += 1
            self._total_prompt_tokens += prompt_tokens
            self._total_completion_tokens += completion_tokens
            self._latencies_ms.append(duration_ms)

    def record_tool_execution(self):
        """Record a tool execution."""
        with self._lock:
            self._total_tool_calls += 1

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregate summary metrics."""
        with self._lock:
            avg_latency = (sum(self._latencies_ms) / len(self._latencies_ms)) if self._latencies_ms else 0.0
            return {
                "total_llm_calls": self._total_llm_calls,
                "total_tool_calls": self._total_tool_calls,
                "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
                "avg_llm_latency_ms": round(avg_latency, 2),
            }


# Global singleton instance
metrics_tracker = MetricsTracker()
