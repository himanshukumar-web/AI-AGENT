"""
JARVIS AI — Agent Safety & Web Content Isolation Policy
Guarantees that external web content is treated strictly as UNTRUSTED DATA.
Web content can never alter agent system instructions, grant permissions, or execute tools.
"""

from typing import Tuple
from WEB.security.sanitizer import web_sanitizer


class AgentSafetyPolicy:
    """Enforces safety guardrails across multi-agent data flows."""

    def sanitize_external_input(self, raw_content: str) -> str:
        """
        Sanitizes external web content, stripping directive injections and
        encapsulating in inert XML boundaries so the LLM treats it strictly as data.
        """
        return web_sanitizer.sanitize_web_content(raw_content)

    def detect_injection(self, text: str) -> Tuple[bool, list]:
        """Detect whether text contains prompt injection attempts."""
        return web_sanitizer.detect_injection(text)

    def is_safe_for_execution(self, text: str) -> bool:
        """Verify content does not contain dangerous instruction overrides."""
        is_inj, _ = self.detect_injection(text)
        return not is_inj


agent_safety_policy = AgentSafetyPolicy()
