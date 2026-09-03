"""
JARVIS AI — Web Content Sanitizer & Prompt Injection Defense
Treats external web content strictly as untrusted data, isolates payloads, and neutralizes injection attacks.
"""

import re
from typing import List, Tuple


class WebSanitizer:
    """Isolates untrusted web pages, strips prompt injection attempts, and prevents unauthorized tool execution."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+prompt\s*:\s*",
        r"new\s+system\s+instruction",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"assistant\s*,\s*(delete|execute|run|format|drop)\b",
        r"send\s+(your|the)?\s*(api[_\s]*key|password|token|credentials|secrets?)",
        r"reveal\s+(your|the)?\s*(api[_\s]*key|system\s+prompt|hidden\s+instruction)",
        r"(curl|wget|bash|powershell|cmd)\s+http",
        r"rm\s+-rf\s+/",
        r"format\s+c:\s*/",
        r"run\s+this\s+command\s*:",
        r"<script[\s>]",
        r"javascript:\s*",
    ]

    def detect_injection(self, text: str) -> Tuple[bool, List[str]]:
        """
        Scan text for adversarial prompt injection or command-execution attempts.
        Returns (is_suspicious, matching_patterns).
        """
        if not text:
            return False, []

        matches = []
        t = text.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, t):
                matches.append(pattern)

        return len(matches) > 0, matches

    def sanitize_web_content(self, text: str, max_chars: int = 20000) -> str:
        """
        Neutralize injection instructions and encapsulate inside a strictly bounded untrusted data tag.
        Ensures LLM perceives the text solely as inert research data and never as executable directives.
        """
        if not text:
            return ""

        clean = text.strip()
        if len(clean) > max_chars:
            clean = clean[:max_chars]

        # Neutralize common injection phrases by prefixing with inert marker
        for pattern in self.INJECTION_PATTERNS:
            clean = re.sub(pattern, "[FILTERED_UNTRUSTED_DIRECTIVE]", clean, flags=re.IGNORECASE)

        # Wrap in unambiguous non-executable data boundary
        return (
            "<untrusted_external_web_data context='evidence_only' do_not_execute='true'>\n"
            f"{clean}\n"
            "</untrusted_external_web_data>"
        )

    def is_safe_for_synthesis(self, text: str) -> bool:
        """Verify that web content does not contain dangerous active payloads."""
        is_suspicious, _ = self.detect_injection(text)
        return not is_suspicious


# Global singleton instance
web_sanitizer = WebSanitizer()
