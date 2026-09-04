"""
JARVIS AI — Agent Delegator
Dynamically routes subtasks to the optimal specialized agent based on capability scoring and tool access.
"""

from typing import Any, Dict, List, Optional
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_registry import agent_registry
import AGENTS.agents


class AgentDelegator:
    """Matches subtasks to specialized agents based on capability scoring."""

    KEYWORD_MAP = {
        "research": ["research", "search", "compare", "sources", "fact", "citations", "find"],
        "automation": ["automation", "schedule", "remind", "timer", "alarm", "youtube", "recurring"],
        "browser": ["browser", "website", "url", "open site", "navigate"],
        "computer": ["screen", "desktop", "click", "mouse", "keyboard", "window", "type", "scroll"],
        "system": ["time", "battery", "weather", "ip", "internet", "status", "doctor", "diagnostics", "app"],
        "memory": ["memory", "remember", "recall", "forget", "preference", "store"],
        "conversation": ["explain", "chat", "tell me", "talk", "clarify"],
    }

    def resolve_agent(self, task_action: str, agent_hint: Optional[str] = None, prompt: str = "") -> Optional[BaseAgent]:
        """Resolve the most suitable agent instance for a subtask."""
        # 1. If explicit agent hint provided and valid
        if agent_hint:
            agent = agent_registry.get_agent(agent_hint)
            if agent:
                return agent

        # 2. Match by declared capability in registry
        candidates = agent_registry.find_agents_by_capability(task_action)
        if candidates:
            return candidates[0]

        # 3. Match by action or tool affiliation
        tool_agent = agent_registry.find_agent_for_tool(task_action)
        if tool_agent:
            return tool_agent

        # 4. Keyword heuristic resolution
        combined = f"{task_action} {prompt}".lower()
        for agent_name, keywords in self.KEYWORD_MAP.items():
            if any(kw in combined for kw in keywords):
                agent = agent_registry.get_agent(agent_name)
                if agent:
                    return agent

        # 5. Default fallback to conversation agent
        return agent_registry.get_agent("conversation")


agent_delegator = AgentDelegator()
