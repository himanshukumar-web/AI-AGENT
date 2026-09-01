"""
JARVIS AI — Memory Skill Module
Encapsulates long-term fact storage, contextual memory recall, deletion, and cleanup.
"""

from typing import Any, Dict, Optional
from BRAIN.MEMORY.memory_manager import memory_manager
from SKILLS.base_skill import BaseSkill, SkillCategory


class MemorySkill(BaseSkill):
    """Provides memory persistence, fact recollection, and knowledge curation."""

    def __init__(self):
        super().__init__(
            name="memory",
            description="Stores user preferences, recalls persistent facts, and prunes stale data.",
            category=SkillCategory.MEMORY,
        )

    def initialize(self):
        def _remember(key: str, value: str, category: str = "preference", importance: int = 3) -> Dict[str, Any]:
            success = memory_manager.store_fact(key=key, value=value, category=category, importance=importance)
            if success:
                return {"success": True, "data": {"key": key, "value": value, "message": f"I've remembered that {key} is {value}."}, "error": None}
            return {"success": False, "data": None, "error": "Could not store sensitive information or invalid key."}

        self.register_tool(
            name="memory.remember",
            description="Store a personal preference, trait, or fact in persistent memory.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The fact or preference identifier."},
                    "value": {"type": "string", "description": "The information to remember."},
                    "category": {"type": "string", "description": "Category ('preference', 'fact', 'routine')."},
                    "importance": {"type": "integer", "description": "Importance rating from 1 to 5."}
                },
                "required": ["key", "value"],
            },
            handler=_remember,
            risk_level="medium",
            aliases=["remember_fact", "memory.save"],
        )

        def _recall(query: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
            facts = memory_manager.recall_facts(query=query, category=category)
            return {"success": True, "data": {"count": len(facts), "facts": facts}, "error": None}

        self.register_tool(
            name="memory.recall",
            description="Search or recall stored facts from memory.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword or topic."},
                    "category": {"type": "string", "description": "Filter by category."}
                }
            },
            handler=_recall,
            risk_level="low",
            aliases=["recall_memory", "memory.search", "memory.list"],
        )

        def _forget(query: str) -> Dict[str, Any]:
            count = memory_manager.forget_facts_matching(query)
            return {"success": True, "data": {"forgotten_count": count, "message": f"Removed {count} memory record(s) matching '{query}'."}, "error": None}

        self.register_tool(
            name="memory.forget",
            description="Forget or delete stored memories matching a query.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The keyword or topic to forget."}
                },
                "required": ["query"],
            },
            handler=_forget,
            risk_level="high",
            aliases=["forget_memory", "memory.delete"],
        )

        def _cleanup(days: int = 30) -> Dict[str, Any]:
            deleted_turns = memory_manager.cleanup_old_history(days=days)
            return {"success": True, "data": {"deleted_turns": deleted_turns, "message": f"Cleaned up {deleted_turns} old dialogue turns."}, "error": None}

        self.register_tool(
            name="memory.cleanup",
            description="Prune old low-importance conversation turns to maintain optimal memory performance.",
            parameters={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Age in days beyond which to prune low-priority history."}
                }
            },
            handler=_cleanup,
            risk_level="medium",
            aliases=["memory.prune"],
        )
