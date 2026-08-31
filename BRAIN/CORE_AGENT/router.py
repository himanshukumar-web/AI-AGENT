"""
JARVIS AI — Intelligent Intent & Task Router
Categorizes user requests to direct execution pipelines without unnecessary LLM latency.
"""

from enum import Enum
import re
from typing import Any, Dict, Optional, Tuple


class RouteCategory(Enum):
    INTERRUPT = "interrupt"
    SIMPLE_COMMAND = "simple_command"
    MEMORY_COMMAND = "memory_command"
    AUTOMATION = "automation"
    SEARCH_RESEARCH = "search_research"
    MULTI_STEP_TASK = "multi_step_task"
    QUESTION_KNOWLEDGE = "question_knowledge"
    CONVERSATION = "conversation"


class IntelligentRouter:
    """Classifies user requests into optimal processing channels."""

    INTERRUPT_KEYWORDS = ["stop", "cancel", "cancel that", "jarvis stop", "chup", "ruko", "stop now", "abort"]

    MEMORY_REMEMBER_PATTERNS = [
        r"^remember\s+that\s+(.*)",
        r"^remember\s+(.*)",
        r"^save\s+preference\s+(.*)",
        r"^yaad\s+rakho\s+(.*)",
    ]

    MEMORY_FORGET_PATTERNS = [
        r"^forget\s+what\s+i\s+told\s+you\s+about\s+(.*)",
        r"^forget\s+about\s+(.*)",
        r"^forget\s+(.*)",
        r"^bhool\s+jao\s+(.*)",
    ]

    MEMORY_RECALL_PATTERNS = [
        r"^what\s+do\s+you\s+remember.*",
        r"^show\s+my\s+preferences.*",
        r"^what\s+are\s+my\s+preferences.*",
        r"^list\s+my\s+memories.*",
    ]

    MULTI_STEP_INDICATORS = [
        " and then ", " then ", " after that ",
        "compare", "find the best", "and save the result",
        "and summarize", "and create an automation",
    ]

    def route(self, text: str, active_topic: Optional[str] = None) -> Tuple[RouteCategory, Dict[str, Any]]:
        """
        Classify raw input text into RouteCategory and relevant routing metadata.
        """
        if not text:
            return RouteCategory.CONVERSATION, {}

        t = text.lower().strip()

        # 1. Check for immediate Interruption
        if t in self.INTERRUPT_KEYWORDS or any(t == kw for kw in self.INTERRUPT_KEYWORDS):
            return RouteCategory.INTERRUPT, {"action": "stop"}

        # 2. Check for Memory Commands
        for p in self.MEMORY_REMEMBER_PATTERNS:
            m = re.match(p, t)
            if m:
                return RouteCategory.MEMORY_COMMAND, {"sub_type": "remember", "content": m.group(1).strip()}

        for p in self.MEMORY_FORGET_PATTERNS:
            m = re.match(p, t)
            if m:
                return RouteCategory.MEMORY_COMMAND, {"sub_type": "forget", "query": m.group(1).strip()}

        for p in self.MEMORY_RECALL_PATTERNS:
            if re.match(p, t):
                return RouteCategory.MEMORY_COMMAND, {"sub_type": "recall", "query": None}

        # 3. Check for Multi-Step Planning Tasks
        if any(ind in t for ind in self.MULTI_STEP_INDICATORS) and len(t.split()) > 5:
            return RouteCategory.MULTI_STEP_TASK, {"raw_prompt": text}

        # 4. Check for Custom Automations
        if any(w in t for w in ["create automation", "new automation", "list automation", "show automation", "delete automation", "disable automation", "run automation", "my automation", "remind me every", "every morning at", "every day at"]):
            return RouteCategory.AUTOMATION, {"command": text}

        # 5. Check for Search / Deep Research
        if any(t.startswith(kw) for kw in ["define ", "brief ", "research ", "teach me ", "deep search "]):
            return RouteCategory.SEARCH_RESEARCH, {"query": t}

        # 6. Check for Simple Deterministic Commands
        simple_patterns = [
            "what time", "what's the time", "current time", "tell me time",
            "battery", "battery percentage", "battery status", "check battery",
            "tell me a joke", "joke", "make me laugh",
            "give me advice", "advice", "suggestion",
            "my ip", "ip address", "what is my ip",
            "internet status", "am i online",
            "open youtube", "open google", "open notepad", "open calculator",
            "hello", "hi", "hey jarvis", "goodbye", "bye", "exit", "quit",
        ]
        if any(t == sp or t.startswith(sp + " ") for sp in simple_patterns):
            return RouteCategory.SIMPLE_COMMAND, {"direct": True}

        # 7. Check for Questions
        if t.startswith(("what is", "who is", "where is", "when did", "how does", "why is", "which is", "can you explain")):
            return RouteCategory.QUESTION_KNOWLEDGE, {"question": text}

        # 8. Default to Conversational LLM reasoning
        return RouteCategory.CONVERSATION, {"input": text}


# Global singleton instance
intelligent_router = IntelligentRouter()
