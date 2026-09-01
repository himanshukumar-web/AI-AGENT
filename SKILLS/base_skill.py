"""
JARVIS AI — Base Skill Architecture (Phase 4)
Abstract foundation for modular, discoverable, and extensible skills/plugins.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class SkillCategory(Enum):
    SYSTEM = "system"
    MEDIA = "media"
    WEB = "web"
    AUTOMATION = "automation"
    MEMORY = "memory"
    RESEARCH = "research"
    UTILITY = "utility"


class BaseSkill(ABC):
    """Abstract base class for all JARVIS skills."""

    def __init__(
        self,
        name: str,
        description: str,
        category: SkillCategory = SkillCategory.UTILITY,
        version: str = "1.0.0",
        enabled: bool = True,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self.enabled = enabled
        self._tools: Dict[str, Dict[str, Any]] = {}
        self.initialize()

    def initialize(self):
        """Optional lifecycle hook called on instantiation."""
        pass

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Dict[str, Any]],
        risk_level: str = "low",
        aliases: Optional[List[str]] = None,
    ):
        """Register a discrete capability tool within this skill."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
            "risk_level": risk_level,
            "aliases": aliases or [],
            "skill": self.name,
        }

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return all tools provided by this skill."""
        return self._tools if self.enabled else {}

    def get_info(self) -> Dict[str, Any]:
        """Return metadata summary for the skill."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "enabled": self.enabled,
            "tool_count": len(self._tools),
            "tools": list(self._tools.keys()),
        }

    def enable(self):
        """Enable the skill."""
        self.enabled = True

    def disable(self):
        """Disable the skill."""
        self.enabled = False
