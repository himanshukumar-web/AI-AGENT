"""
JARVIS AI — Base Agent Contract
Formal specification that every specialized agent in JARVIS must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult


class BaseAgent(ABC):
    """
    Standard interface for specialized agents.
    Enforces clear responsibilities, tool whitelisting, and structured result contracts.
    """

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None,
        risk_level: str = "LOW",
        max_steps: int = 5,
        timeout: float = 30.0,
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.allowed_tools = allowed_tools or []
        self.risk_level = risk_level.upper()
        self.max_steps = max_steps
        self.timeout = timeout

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute agent logic for the assigned subtask.
        Must return a structured AgentResult (never a loose raw string).
        """
        pass

    def can_handle(self, capability: str) -> bool:
        """Check whether this agent possesses the requested capability."""
        cap_clean = capability.lower().strip()
        return any(c.lower() == cap_clean or cap_clean in c.lower() for c in self.capabilities)

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Enforce strict tool whitelisting. An agent cannot call tools outside its declared list."""
        t_clean = tool_name.lower().strip()
        return any(t.lower() == t_clean for t in self.allowed_tools)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent metadata for introspection and registry."""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "allowed_tools": self.allowed_tools,
            "risk_level": self.risk_level,
            "max_steps": self.max_steps,
            "timeout": self.timeout,
        }
