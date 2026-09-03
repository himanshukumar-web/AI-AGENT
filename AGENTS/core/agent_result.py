"""
JARVIS AI — Structured Agent Result
Defines explicit, typed outcomes for agent executions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_CONFIRMATION = "needs_confirmation"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Structured result returned by every specialized agent execution."""
    success: bool
    status: AgentStatus = AgentStatus.COMPLETED
    output: Any = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_required: bool = False
    verification_criteria: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value if isinstance(self.status, AgentStatus) else str(self.status),
            "output": self.output,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "metadata": self.metadata,
            "verification_required": self.verification_required,
            "verification_criteria": self.verification_criteria,
        }

    @classmethod
    def ok(cls, output: Any, metadata: Optional[Dict[str, Any]] = None, artifacts: Optional[List[Dict[str, Any]]] = None, verification_required: bool = False, verification_criteria: Optional[Dict[str, Any]] = None) -> "AgentResult":
        """Factory for successful agent outcome."""
        return cls(
            success=True,
            status=AgentStatus.COMPLETED,
            output=output,
            artifacts=artifacts or [],
            metadata=metadata or {},
            verification_required=verification_required,
            verification_criteria=verification_criteria,
        )

    @classmethod
    def fail(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "AgentResult":
        """Factory for failed agent outcome."""
        return cls(
            success=False,
            status=AgentStatus.FAILED,
            output=None,
            errors=[error],
            metadata=metadata or {},
        )

    @classmethod
    def needs_confirmation(cls, action_name: str, details: str, risk_level: str = "HIGH", metadata: Optional[Dict[str, Any]] = None) -> "AgentResult":
        """Factory for actions requiring human confirmation."""
        return cls(
            success=False,
            status=AgentStatus.NEEDS_CONFIRMATION,
            output={"action": action_name, "details": details, "risk_level": risk_level},
            metadata=metadata or {},
        )
