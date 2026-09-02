"""
JARVIS AI — Central Skill Registry (Phase 4)
Orchestrates modular skills, discovery, dynamic enabling/disabling, and capability introspection.
"""

from typing import Any, Dict, List, Optional
from SKILLS.base_skill import BaseSkill


class SkillRegistry:
    """Manages the lifecycle and discovery of modular JARVIS skills."""

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._load_built_in_skills()

    def _load_built_in_skills(self):
        """Auto-discover and load built-in domain skills."""
        try:
            from SKILLS.system_skill import SystemSkill
            from SKILLS.browser_skill import BrowserSkill
            from SKILLS.youtube_skill import YouTubeSkill
            from SKILLS.weather_skill import WeatherSkill
            from SKILLS.automation_skill import AutomationSkill
            from SKILLS.memory_skill import MemorySkill
            from SKILLS.research_skill import ResearchSkill
            from SKILLS.computer_skill import ComputerSkill

            self.register(SystemSkill())
            self.register(BrowserSkill())
            self.register(YouTubeSkill())
            self.register(WeatherSkill())
            self.register(AutomationSkill())
            self.register(MemorySkill())
            self.register(ResearchSkill())
            self.register(ComputerSkill())
        except Exception as e:
            pass

    def register(self, skill: BaseSkill):
        """Register a new skill instance."""
        self._skills[skill.name.lower()] = skill

    def get(self, name: str) -> Optional[BaseSkill]:
        """Retrieve a registered skill by name."""
        return self._skills.get(name.lower())

    def list(self, only_enabled: bool = True) -> List[Dict[str, Any]]:
        """List metadata for all registered skills."""
        results = []
        for s in self._skills.values():
            if not only_enabled or s.enabled:
                results.append(s.get_info())
        return results

    def enable(self, name: str) -> bool:
        """Enable a registered skill."""
        skill = self.get(name)
        if skill:
            skill.enable()
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a registered skill."""
        skill = self.get(name)
        if skill:
            skill.disable()
            return True
        return False

    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Collect all active tools across enabled skills."""
        tools = {}
        for skill in self._skills.values():
            if skill.enabled:
                tools.update(skill.get_tools())
        return tools

    def get_capabilities_summary(self) -> str:
        """Generate a concise, natural summary of active capabilities."""
        active = [s for s in self._skills.values() if s.enabled]
        if not active:
            return "No skills are currently active."

        caps = []
        for s in active:
            tool_names = ", ".join(list(s.get_tools().keys())[:3])
            caps.append(f"• {s.name.capitalize()} ({s.description})")

        return "Here is what I can do:\n" + "\n".join(caps)


# Global singleton instance
skill_registry = SkillRegistry()
