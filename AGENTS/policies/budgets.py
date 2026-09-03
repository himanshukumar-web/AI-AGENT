"""
JARVIS AI — Agent Budget System
Prevents infinite autonomous loops by strictly enforcing step, tool, runtime, and retry budgets.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass
class AgentBudget:
    """Configurable limits for an autonomous multi-agent task."""
    max_steps: int = 20
    max_tool_calls: int = 50
    max_llm_calls: int = 30
    max_runtime: float = 120.0
    max_retries: int = 3
    max_cost: float = 1.0


class BudgetTracker:
    """Tracks consumption against an AgentBudget."""

    def __init__(self, budget: AgentBudget):
        self.budget = budget
        self.steps_taken: int = 0
        self.tool_calls_made: int = 0
        self.llm_calls_made: int = 0
        self.retries_made: int = 0
        self.start_time: float = time.time()

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time

    def is_expired(self) -> bool:
        return self.get_elapsed_time() > self.budget.max_runtime

    def can_execute_step(self) -> Tuple[bool, str]:
        if self.steps_taken >= self.budget.max_steps:
            return False, f"Maximum steps budget ({self.budget.max_steps}) exceeded."
        if self.is_expired():
            return False, f"Maximum task runtime ({self.budget.max_runtime}s) exceeded."
        return True, ""

    def record_step(self):
        self.steps_taken += 1

    def can_call_tool(self) -> Tuple[bool, str]:
        if self.tool_calls_made >= self.budget.max_tool_calls:
            return False, f"Maximum tool calls budget ({self.budget.max_tool_calls}) exceeded."
        if self.is_expired():
            return False, f"Maximum task runtime ({self.budget.max_runtime}s) exceeded."
        return True, ""

    def record_tool_call(self):
        self.tool_calls_made += 1

    def can_call_llm(self) -> Tuple[bool, str]:
        if self.llm_calls_made >= self.budget.max_llm_calls:
            return False, f"Maximum LLM calls budget ({self.budget.max_llm_calls}) exceeded."
        if self.is_expired():
            return False, f"Maximum task runtime ({self.budget.max_runtime}s) exceeded."
        return True, ""

    def record_llm_call(self):
        self.llm_calls_made += 1

    def can_retry(self) -> Tuple[bool, str]:
        if self.retries_made >= self.budget.max_retries:
            return False, f"Maximum retries ({self.budget.max_retries}) exceeded."
        return True, ""

    def record_retry(self):
        self.retries_made += 1

    def get_summary(self) -> Dict[str, Any]:
        return {
            "steps": f"{self.steps_taken}/{self.budget.max_steps}",
            "tool_calls": f"{self.tool_calls_made}/{self.budget.max_tool_calls}",
            "llm_calls": f"{self.llm_calls_made}/{self.budget.max_llm_calls}",
            "retries": f"{self.retries_made}/{self.budget.max_retries}",
            "elapsed_seconds": round(self.get_elapsed_time(), 2),
            "max_runtime_seconds": self.budget.max_runtime,
        }
