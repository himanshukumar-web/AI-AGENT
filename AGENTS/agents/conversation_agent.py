"""
JARVIS AI — Specialized Conversation Agent
Handles general conversation, explanations, follow-up inquiries, and contextual reasoning.
"""

from typing import Any, Dict
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.LLM.provider_manager import provider_manager
from BRAIN.MEMORY.memory_manager import memory_manager
from BRAIN.PROMPTS.system_prompt import get_system_prompt


class ConversationAgent(BaseAgent):
    """Specialized agent for conversational dialog and explanations."""

    def __init__(self):
        super().__init__(
            name="conversation",
            description="Handles general conversation, explanations, follow-ups, and natural dialogue.",
            capabilities=["conversation", "explanation", "follow_up", "dialogue", "summarization"],
            allowed_tools=["action.history", "memory.recall"],
            risk_level="LOW",
            max_steps=3,
            timeout=30.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Process conversational prompt using LLM provider."""
        prompt = context.get_input("prompt", context.user_request)

        # Budget check
        can_llm, reason = context.budget_tracker.can_call_llm()
        if not can_llm:
            return AgentResult.fail(reason)

        try:
            context.budget_tracker.record_llm_call()
            active_prov = provider_manager.get_active_provider()
            relevant_facts = memory_manager.search_relevant_context(prompt)
            sys_prompt = get_system_prompt(custom_facts=relevant_facts)

            resp = active_prov.generate(
                prompt=prompt,
                system_prompt=sys_prompt,
                temperature=0.7,
                max_tokens=400,
            )
            text = resp.text.strip() if resp and resp.text else "I understand."
            return AgentResult.ok(output=text, metadata={"model": active_prov.model_name})
        except Exception as e:
            return AgentResult.fail(f"Conversation error: {e}")
