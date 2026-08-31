"""
JARVIS AI — Conversation & Multi-Turn State Manager
Tracks dialogue history, active context (current app/topic), and bounded context windows.
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from config import MAX_CONTEXT_TURNS
from BRAIN.MEMORY.memory_manager import memory_manager


class ConversationManager:
    """Manages active conversation session, bounded turns, and situational state."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._history: List[Dict[str, str]] = []
        self._context_state: Dict[str, Any] = {
            "active_topic": None,       # e.g. 'youtube', 'weather', 'automation', 'browser'
            "last_action": None,        # e.g. 'open_website', 'search_google'
            "last_tool_result": None,
            "last_entity": None,        # e.g. 'Arijit Singh', 'Delhi'
        }

    def add_user_message(self, text: str):
        """Record user input in current context."""
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
        """Update active situational state."""
        self._context_state.update(kwargs)

    def get_context_state(self) -> Dict[str, Any]:
        """Get current situational context."""
        return self._context_state.copy()

    def get_history_for_llm(self) -> List[Dict[str, str]]:
        """Return sliding context window for LLM prompt."""
        return self._history[-MAX_CONTEXT_TURNS * 2:]

    def _prune_history(self):
        """Keep bounded in-memory context window."""
        max_messages = MAX_CONTEXT_TURNS * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    def resolve_follow_up_hint(self, raw_input: str) -> Optional[str]:
        """
        Detect contextual follow-ups like 'what about tomorrow' or 'search for X'
        and provide extra context hint if helpful.
        """
        text = raw_input.lower().strip()
        active_topic = self._context_state.get("active_topic")

        if active_topic == "youtube" and (text.startswith("search for") or text.startswith("play ")):
            return f"Context: YouTube is currently active."
        if active_topic == "weather" and any(w in text for w in ["tomorrow", "next week", "later", "kal"]):
            return f"Context: User is inquiring about weather in {self._context_state.get('last_entity', 'current city')}."

        return None

    def reset(self):
        """Reset conversation session."""
        self.session_id = str(uuid.uuid4())[:8]
        self._history.clear()
        self._context_state = {
            "active_topic": None,
            "last_action": None,
            "last_tool_result": None,
            "last_entity": None,
        }


# Global singleton instance
conversation_manager = ConversationManager()
