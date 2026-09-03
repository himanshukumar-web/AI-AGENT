"""
JARVIS AI — Intelligent Intent & Task Router (Brain 3.0)
Categorizes user requests to direct execution pipelines without unnecessary LLM latency.
Preserves fast local processing for deterministic commands and delegates complex reasoning.
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

    INTERRUPT_KEYWORDS = [
        "stop", "cancel", "cancel that", "jarvis stop", "chup", "ruko",
        "roko", "stop now", "abort", "shut up", "quiet", "silence", "stop speaking",
        "stop research", "cancel research", "abort research"
    ]

    MEMORY_REMEMBER_PATTERNS = [
        r"^remember\s+that\s+(.*)",
        r"^remember\s+(.*)",
        r"^save\s+preference\s+(.*)",
        r"^yaad\s+rakho\s+ki\s+(.*)",
        r"^yaad\s+rakho\s+(.*)",
    ]

    MEMORY_FORGET_PATTERNS = [
        r"^forget\s+what\s+i\s+told\s+you\s+about\s+(.*)",
        r"^forget\s+about\s+(.*)",
        r"^forget\s+preference\s+(.*)",
        r"^forget\s+(.*)",
        r"^bhool\s+jao\s+(.*)",
    ]

    MEMORY_RECALL_PATTERNS = [
        r"^what\s+do\s+you\s+remember.*",
        r"^show\s+my\s+preferences.*",
        r"^what\s+are\s+my\s+preferences.*",
        r"^list\s+my\s+memories.*",
        r"^kya\s+yaad\s+hai.*",
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
        if any(w in t for w in ["create automation", "new automation", "list automation", "show automation", "show my automations", "delete automation", "disable automation", "run automation", "my automation", "remind me every", "every morning at", "every day at", "subah 9 baje"]):
            return RouteCategory.AUTOMATION, {"command": text}

        # 5. Check for Research Memory, Follow-ups, and Monitoring
        if t in ["save this research", "save research", "save the research"]:
            return RouteCategory.SEARCH_RESEARCH, {"sub_type": "save_research"}

        if t in ["continue that research", "continue research", "continue the research", "follow up on that research"]:
            return RouteCategory.SEARCH_RESEARCH, {"sub_type": "continue_research"}

        if any(w in t for w in ["check if ", "check whether "]) and any(k in t for k in ["changed", "has changed", "still current", "updated"]):
            return RouteCategory.SEARCH_RESEARCH, {"sub_type": "check_changed", "query": text}

        # Check for Comparison
        if t.startswith("compare ") or " vs " in t:
            return RouteCategory.SEARCH_RESEARCH, {"sub_type": "compare", "query": text}

        # Check for Deep / Quick / General Research
        research_prefixes = [
            "do deep research on ", "deep research on ", "deep research ",
            "do research on ", "quick research on ", "quickly tell me ",
            "research ", "deep search ", "investigate ", "brief me on ",
            "teach me about ", "find official documentation for ", "search for "
        ]
        for rp in research_prefixes:
            if t.startswith(rp):
                q = t[len(rp):].strip()
                mode = "deep" if "deep" in rp else ("quick" if "quick" in rp else "standard")
                return RouteCategory.SEARCH_RESEARCH, {"sub_type": "research", "query": q, "mode": mode}

        if any(t.startswith(kw) for kw in ["define ", "brief "]):
            return RouteCategory.SEARCH_RESEARCH, {"sub_type": "research", "query": t, "mode": "quick"}

        # 6. Check for Simple Deterministic Commands (English & Hinglish)
        simple_patterns = [
            "what time", "what's the time", "current time", "tell me time", "time batao", "kitne baje",
            "battery", "battery percentage", "battery status", "check battery", "battery kitni hai",
            "weather", "how is the weather", "tell me the weather", "mausam batao", "weather batao",
            "tell me a joke", "joke", "make me laugh", "joke sunao",
            "give me advice", "advice", "suggestion", "motivate me", "advice do",
            "my ip", "ip address", "what is my ip", "find my ip",
            "internet status", "am i online", "check internet",
            "open youtube", "youtube open", "youtube kholo",
            "open google", "google open", "google kholo",
            "open notepad", "notepad kholo", "open calculator", "calc kholo",
            "run diagnostics", "diagnostics", "check health", "doctor",
            "show my recent actions", "show recent actions", "recent actions", "action history",
            "what can you do", "what are your capabilities", "capabilities", "what are your skills", "show skills", "skills",
            "what can you do with my computer", "computer capabilities",
            "what's on my screen", "what is on my screen", "describe my screen", "screen pe kya hai",
            "what application is open", "what app is open", "which app is open", "which window is open",
            "scroll down", "scroll up",
            "status", "jarvis status", "system status",
            "hello", "hi", "hey jarvis", "namaste", "goodbye", "bye", "exit", "quit",
        ]
        if any(t == sp or t.startswith(sp + " ") for sp in simple_patterns):
            return RouteCategory.SIMPLE_COMMAND, {"direct": True}


        # 7. Check for Questions
        if t.startswith(("what is", "who is", "where is", "when did", "how does", "why is", "which is", "can you explain", "kya hai", "kaun hai")):
            return RouteCategory.QUESTION_KNOWLEDGE, {"question": text}

        # 8. Default to Conversational LLM reasoning
        return RouteCategory.CONVERSATION, {"input": text}


# Global singleton instance
intelligent_router = IntelligentRouter()

