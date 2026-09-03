"""
JARVIS AI — Structured Inter-Agent Message
Provides decoupled, traceable communication between agents.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AgentMessage:
    """Standardized message format exchanged between agents and orchestrator."""
    sender: str
    receiver: str
    task_id: str
    message_type: str  # e.g., "TASK_REQUEST", "TASK_RESULT", "STATUS_UPDATE", "VERIFY_REQUEST"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "task_id": self.task_id,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }
