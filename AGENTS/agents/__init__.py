"""
JARVIS AI — Specialized Agent Suite
Registers all 9 specialized agents in the AgentRegistry on import.
"""

from AGENTS.core.agent_registry import agent_registry
from AGENTS.agents.conversation_agent import ConversationAgent
from AGENTS.agents.research_agent import ResearchAgent
from AGENTS.agents.automation_agent import AutomationAgent
from AGENTS.agents.browser_agent import BrowserAgent
from AGENTS.agents.computer_agent import ComputerAgent
from AGENTS.agents.system_agent import SystemAgent
from AGENTS.agents.memory_agent import MemoryAgent
from AGENTS.agents.planner_agent import PlannerAgent
from AGENTS.agents.verification_agent import VerificationAgent

# Initialize and register singleton instances
conversation_agent = ConversationAgent()
research_agent = ResearchAgent()
automation_agent = AutomationAgent()
browser_agent = BrowserAgent()
computer_agent = ComputerAgent()
system_agent = SystemAgent()
memory_agent = MemoryAgent()
planner_agent = PlannerAgent()
verification_agent = VerificationAgent()

ALL_AGENTS = [
    conversation_agent,
    research_agent,
    automation_agent,
    browser_agent,
    computer_agent,
    system_agent,
    memory_agent,
    planner_agent,
    verification_agent,
]

for agent in ALL_AGENTS:
    agent_registry.register(agent)

__all__ = [
    "ConversationAgent",
    "ResearchAgent",
    "AutomationAgent",
    "BrowserAgent",
    "ComputerAgent",
    "SystemAgent",
    "MemoryAgent",
    "PlannerAgent",
    "VerificationAgent",
    "conversation_agent",
    "research_agent",
    "automation_agent",
    "browser_agent",
    "computer_agent",
    "system_agent",
    "memory_agent",
    "planner_agent",
    "verification_agent",
    "ALL_AGENTS",
]
