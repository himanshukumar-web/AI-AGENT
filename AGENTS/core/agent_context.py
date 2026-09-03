"""
JARVIS AI — Agent Execution Context
Carries shared state, parameters, budgets, and cancellation tokens to executing agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from AGENTS.policies.budgets import BudgetTracker, AgentBudget


@dataclass
class AgentContext:
    """Execution context provided to an agent for a specific task step."""
    task_id: str
    step_id: str
    user_request: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    budget_tracker: Optional[BudgetTracker] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.budget_tracker is None:
            self.budget_tracker = BudgetTracker(AgentBudget())

    def get_input(self, key: str, default: Any = None) -> Any:
        """Get input parameter for this specific step."""
        return self.inputs.get(key, default)

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get data saved by preceding agents in the task graph."""
        return self.shared_memory.get(key, default)

    def set_shared(self, key: str, value: Any):
        """Store output data for downstream agents in the task graph."""
        self.shared_memory[key] = value

    def is_cancelled(self) -> bool:
        """Check if current task was cancelled by user or emergency stop."""
        try:
            from BRAIN.CORE_AGENT.task_state import task_state_manager
            return task_state_manager.is_interrupted()
        except Exception:
            return False
