"""
JARVIS AI — Conversation & Multi-Turn State Manager
Tracks dialogue history, active topic, situational state, and recent search results for ordinal resolution.
"""

import json
import re
import uuid
from typing import Any, Dict, List, Optional
from config import MAX_CONTEXT_TURNS
from BRAIN.MEMORY.memory_manager import memory_manager


class ConversationManager:
    """Manages active conversation session, bounded context window, and situational state."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._history: List[Dict[str, str]] = []
        self._context_state: Dict[str, Any] = {
            "active_topic": None,       # 'youtube', 'weather', 'automation', 'browser', 'planner'
            "last_action": None,        # 'youtube.search', 'browser.open', etc.
            "last_tool_result": None,
            "last_search_results": [],  # List of items returned in last search
            "last_entity": None,
        }

    def add_user_message(self, text: str):
        """Record user message in current session."""
        self._history.append({"role": "user", "content": text})
        memory_manager.log_turn(self.session_id, "user", text)
        self._prune_history()

    def add_assistant_message(self, text: str, tool_calls: Optional[List[Any]] = None):
        """Record assistant response and optional tool metadata."""
        self._history.append({"role": "assistant", "content": text})
        tc_json = json.dumps([str(tc) for tc in tool_calls]) if tool_calls else None
        memory_manager.log_turn(self.session_id, "assistant", text, tc_json)
        self._prune_history()

    def set_context_state(self, **kwargs):
        """Update situational state."""
        self._context_state.update(kwargs)

    def get_context_state(self) -> Dict[str, Any]:
        """Get current situational context."""
        return self._context_state.copy()

    def set_search_results(self, results: List[str]):
        """Save recent search results for ordinal follow-up commands (e.g. 'play the 2nd one')."""
        self._context_state["last_search_results"] = results

    def get_search_results(self) -> List[str]:
        """Get recent search results list."""
        return self._context_state.get("last_search_results", [])

    def resolve_ordinal_index(self, text: str) -> Optional[int]:
        """
        Check if text refers to an ordinal item (e.g. 'first', 'second', '3rd', 'last').
        Returns 0-based index if matched.
        """
        t = text.lower()

        # Check 'last' or 'aakhri' first
        if re.search(r'\b(last|aakhri)\b', t):
            results = self.get_search_results()
            if results:
                return len(results) - 1
            return -1

        ordinals = {
            "first": 0, "1st": 0, "pehla": 0,
            "second": 1, "2nd": 1, "doosra": 1,
            "third": 2, "3rd": 2, "teesra": 2,
            "fourth": 3, "4th": 3, "chautha": 3,
            "fifth": 4, "5th": 4, "panchwa": 4,
            "one": 0, "two": 1, "three": 2, "four": 3, "five": 4,
        }
        for word, idx in ordinals.items():
            if re.search(r'\b' + re.escape(word) + r'\b', t):
                return idx

        return None



    def get_history_for_llm(self) -> List[Dict[str, str]]:
        """Return bounded context window."""
        return self._history[-MAX_CONTEXT_TURNS * 2:]

    def _prune_history(self):
        """Bound memory footprint."""
        max_messages = MAX_CONTEXT_TURNS * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    def resolve_follow_up_hint(self, raw_input: str) -> Optional[str]:
        """Provide extra context hints for LLM prompt."""
        text = raw_input.lower().strip()
        active_topic = self._context_state.get("active_topic")
        search_results = self._context_state.get("last_search_results", [])

        if active_topic == "youtube":
            if search_results:
                return f"Context: User is referring to recent YouTube search results: {search_results[:3]}"
            return "Context: YouTube is currently active."

        if active_topic == "weather" and any(w in text for w in ["tomorrow", "later", "kal", "next"]):
            return f"Context: Weather inquiry for {self._context_state.get('last_entity', 'current city')}."

        return None

    def reset(self):
        """Reset active conversation state."""
        self.session_id = str(uuid.uuid4())[:8]
        self._history.clear()
        self._context_state = {
            "active_topic": None,
            "last_action": None,
            "last_tool_result": None,
            "last_search_results": [],
            "last_entity": None,
        }


# Global singleton instance
conversation_manager = ConversationManager()
