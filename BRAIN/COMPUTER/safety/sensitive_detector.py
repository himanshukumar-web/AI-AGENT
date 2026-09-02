"""
JARVIS AI — Sensitive UI & Secret Protection
Detects password prompts, banking interfaces, credit card fields, and authentication tokens
to prevent unauthorized interaction or leakage to external vision APIs.
"""

import re
from typing import Tuple, List, Set

# Sensitive keywords in titles or form fields
SENSITIVE_PATTERNS = [
    r'\bpassword\b',
    r'\bpasscode\b',
    r'\bpin\b',
    r'\bcvv\b',
    r'\bcvc\b',
    r'\bcredit\s*card\b',
    r'\bdebit\s*card\b',
    r'\bbanking\b',
    r'\bnetbanking\b',
    r'\botp\b',
    r'\b2fa\b',
    r'\bmfa\b',
    r'\bauthenticat(or|ion)\s*code\b',
    r'\bsecurity\s*code\b',
    r'\bprivate\s*key\b',
    r'\bsecret\s*key\b',
    r'\bseed\s*phrase\b',
    r'\bapi[_-]?key\b',
    r'\bbearer\s+[a-zA-Z0-9_\-\.]{15,}\b',
    r'sk-[a-zA-Z0-9]{20,}',
    r'ghp_[a-zA-Z0-9]{20,}',
]

# Sensitive window title keywords
SENSITIVE_WINDOW_KEYWORDS: Set[str] = {
    "login",
    "sign in",
    "password",
    "authenticator",
    "banking",
    "payment",
    "checkout",
    "credit card",
    "security settings",
    "credential manager",
    "bitwarden",
    "1password",
    "keepass",
    "lastpass",
}


class SensitiveUIDetector:
    """Detects sensitive screens, credentials, and protected UI elements."""

    def __init__(self):
        self._compiled_regexes = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

    def is_sensitive_text(self, text: str) -> Tuple[bool, str]:
        """Checks if text contains credentials, card numbers, or passwords."""
        if not text:
            return False, ""
        for regex in self._compiled_regexes:
            match = regex.search(text)
            if match:
                return True, f"Matched sensitive pattern: '{match.group(0)}'"
        return False, ""

    def is_sensitive_window(self, window_title: str) -> Tuple[bool, str]:
        """Checks if window title suggests authentication, banking, or password manager."""
        if not window_title:
            return False, ""
        t_lower = window_title.lower()
        for kw in SENSITIVE_WINDOW_KEYWORDS:
            if kw in t_lower:
                return True, f"Window title contains sensitive keyword: '{kw}'"
        return False, ""

    def redact_sensitive_text(self, text: str) -> str:
        """Sanitizes text by replacing sensitive secrets/tokens with [REDACTED]."""
        if not text:
            return ""
        result = text
        for regex in self._compiled_regexes:
            result = regex.sub("[REDACTED]", result)
        return result

    def should_block_external_vision(self, window_title: str, query: str = "") -> Tuple[bool, str]:
        """Determines if a screenshot should NOT be sent to cloud vision models."""
        is_sens_win, win_reason = self.is_sensitive_window(window_title)
        if is_sens_win:
            return True, f"Sensitive window detected: {win_reason}"

        is_sens_q, q_reason = self.is_sensitive_text(query)
        if is_sens_q:
            return True, f"Sensitive query detected: {q_reason}"

        return False, ""


sensitive_detector = SensitiveUIDetector()
