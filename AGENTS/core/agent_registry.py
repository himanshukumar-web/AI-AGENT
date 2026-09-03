"""
JARVIS AI — Agent Registry
Central catalog of all available specialized agents, their capabilities, and tool permissions.
"""

from typing import Any, Dict, List, Optional
from AGENTS.core.agent import BaseAgent
from AGENTS.policies.permissions import permission_gate


class AgentRegistry:
    """Central registry tracking active specialized agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Register a specialized agent instance."""
        if not isinstance(agent, BaseAgent):
            raise TypeError(f"Expected BaseAgent instance, got {type(agent)}")
        self._agents[agent.name.lower()] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Look up an agent by canonical name."""
        return self._agents.get(name.lower().strip())

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return serialized list of all registered agents and their capabilities."""
        return [agent.to_dict() for agent in self._agents.values()]

    def find_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Find all agents possessing the specified capability."""
        return [agent for agent in self._agents.values() if agent.can_handle(capability)]

    def find_agent_for_tool(self, tool_name: str) -> Optional[BaseAgent]:
        """Find the designated agent authorized to invoke a tool."""
        for agent in self._agents.values():
            if agent.is_tool_allowed(tool_name):
                return agent
        return None

    def validate_tool_execution(self, agent_name: str, tool_name: str) -> bool:
        """Validate if an agent is authorized to call a specific tool."""
        agent = self.get_agent(agent_name)
        if not agent:
            return False
        allowed, _ = permission_gate.check_tool_permission(agent.name, agent.allowed_tools, tool_name)
        return allowed

    def get_capabilities_map(self) -> Dict[str, List[str]]:
        """Return a mapping of agent name -> list of capabilities."""
        return {name: agent.capabilities for name, agent in self._agents.items()}

    def clear(self):
        """Clear registry (used primarily in test teardown)."""
        self._agents.clear()


# Global singleton instance
agent_registry = AgentRegistry()
