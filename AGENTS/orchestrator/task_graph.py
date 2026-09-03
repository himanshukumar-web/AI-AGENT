"""
JARVIS AI — Task Graph & Directed Acyclic Graph (DAG)
Represents complex multi-step agent plans with dependencies, parallel branches, and state tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from AGENTS.core.agent_result import AgentResult, AgentStatus


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """A discrete unit of work within a TaskGraph assigned to a specialized agent."""
    id: str
    agent_name: str
    action: str
    description: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # List of prerequisite TaskNode IDs
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[AgentResult] = None
    retry_count: int = 0
    max_retries: int = 3
    is_critical: bool = True

    def is_ready(self, completed_node_ids: Set[str]) -> bool:
        """Check if all prerequisite dependencies have completed successfully."""
        if self.status != NodeStatus.PENDING:
            return False
        return all(dep in completed_node_ids for dep in self.dependencies)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "action": self.action,
            "description": self.description,
            "inputs": self.inputs,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "is_critical": self.is_critical,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        res_data = data.get("result")
        result = None
        if res_data:
            result = AgentResult(
                success=res_data.get("success", False),
                status=AgentStatus(res_data.get("status", "completed")),
                output=res_data.get("output"),
                artifacts=res_data.get("artifacts", []),
                errors=res_data.get("errors", []),
                metadata=res_data.get("metadata", {}),
            )

        return cls(
            id=data["id"],
            agent_name=data["agent_name"],
            action=data["action"],
            description=data.get("description", ""),
            inputs=data.get("inputs", {}),
            dependencies=data.get("dependencies", []),
            status=NodeStatus(data.get("status", "pending")),
            result=result,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            is_critical=data.get("is_critical", True),
        )


class TaskGraph:
    """Directed Acyclic Graph (DAG) orchestrating multi-agent execution."""

    def __init__(self, title: str = "Multi-Agent Workflow"):
        self.title = title
        self.nodes: Dict[str, TaskNode] = {}

    def add_node(self, node: TaskNode):
        """Add a task node to the graph."""
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[TaskNode]:
        """Retrieve node by ID."""
        return self.nodes.get(node_id)

    def get_completed_node_ids(self) -> Set[str]:
        """Get IDs of all successfully completed nodes."""
        return {nid for nid, n in self.nodes.items() if n.status == NodeStatus.COMPLETED}

    def get_ready_nodes(self) -> List[TaskNode]:
        """Return all nodes whose dependencies are completed and ready to run."""
        completed = self.get_completed_node_ids()
        return [n for n in self.nodes.values() if n.is_ready(completed)]

    def is_completed(self) -> bool:
        """Check if all nodes have reached a terminal state."""
        terminal_states = {NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.CANCELLED, NodeStatus.SKIPPED}
        return all(n.status in terminal_states for n in self.nodes.values())

    def has_failures(self) -> bool:
        """Check if any critical node failed."""
        return any(n.status == NodeStatus.FAILED and n.is_critical for n in self.nodes.values())

    def get_execution_waves(self) -> List[List[TaskNode]]:
        """
        Topological decomposition into parallel execution waves.
        Independent nodes share the same wave and can be dispatched concurrently.
        """
        waves: List[List[TaskNode]] = []
        completed: Set[str] = set()
        remaining: Dict[str, TaskNode] = dict(self.nodes)

        while remaining:
            current_wave = [n for n in remaining.values() if all(dep in completed for dep in n.dependencies)]
            if not current_wave:
                # Cycle or unresolved dependency detected; break gracefully
                waves.append(list(remaining.values()))
                break

            waves.append(current_wave)
            for n in current_wave:
                completed.add(n.id)
                del remaining[n.id]

        return waves

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        graph = cls(title=data.get("title", "Multi-Agent Workflow"))
        nodes_dict = data.get("nodes", {})
        for nid, ndata in nodes_dict.items():
            graph.add_node(TaskNode.from_dict(ndata))
        return graph
