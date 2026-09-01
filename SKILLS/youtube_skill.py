"""
JARVIS AI — YouTube Skill Module
Encapsulates YouTube searching, direct playback, pause/resume, and volume controls.
"""

import webbrowser
from typing import Any, Dict
from SKILLS.base_skill import BaseSkill, SkillCategory


class YouTubeSkill(BaseSkill):
    """Provides rich YouTube video searching, playback, and control capabilities."""

    def __init__(self):
        super().__init__(
            name="youtube",
            description="Searches YouTube, plays tracks/videos, and controls media playback.",
            category=SkillCategory.MEDIA,
        )

    def initialize(self):
        def _youtube_play(query: str) -> Dict[str, Any]:
            import pywhatkit
            pywhatkit.playonyt(query)
            return {"success": True, "data": {"query": query, "message": f"Playing '{query}' on YouTube."}, "error": None}

        self.register_tool(
            name="youtube.play",
            description="Search and play a video or music track directly on YouTube.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The song, artist, or video title to play."}
                },
                "required": ["query"],
            },
            handler=_youtube_play,
            risk_level="medium",
            aliases=["youtube_play", "play_youtube"],
        )

        def _youtube_search(query: str) -> Dict[str, Any]:
            url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(url)
            from BRAIN.MEMORY.conversation_manager import conversation_manager
            simulated_results = [f"{query} - Video 1", f"{query} - Video 2", f"{query} - Video 3"]
            conversation_manager.set_search_results(simulated_results)
            conversation_manager.set_context_state(active_topic="youtube", last_action="youtube.search")
            return {"success": True, "data": {"query": query, "results": simulated_results, "message": f"Searched YouTube for '{query}'."}, "error": None}

        self.register_tool(
            name="youtube.search",
            description="Search YouTube for videos and present the results.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query on YouTube."}
                },
                "required": ["query"],
            },
            handler=_youtube_search,
            risk_level="medium",
            aliases=["search_youtube"],
        )

        def _youtube_pause() -> Dict[str, Any]:
            import pyautogui
            pyautogui.press('k')
            return {"success": True, "data": {"action": "toggle_pause", "message": "Toggled YouTube video play/pause."}, "error": None}

        self.register_tool(
            name="youtube.pause",
            description="Toggle play/pause on the active YouTube video.",
            parameters={"type": "object", "properties": {}},
            handler=_youtube_pause,
            risk_level="medium",
            aliases=["youtube_pause", "pause_video"],
        )

        def _youtube_volume(direction: str = "up") -> Dict[str, Any]:
            import pyautogui
            key = 'up' if direction.lower() == 'up' else 'down'
            for _ in range(3):
                pyautogui.press(key)
            return {"success": True, "data": {"direction": direction, "message": f"Adjusted YouTube volume {direction}."}, "error": None}

        self.register_tool(
            name="youtube.volume",
            description="Adjust YouTube playback volume up or down.",
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"], "description": "Direction ('up' or 'down')."}
                },
                "required": ["direction"],
            },
            handler=_youtube_volume,
            risk_level="medium",
            aliases=["youtube_volume", "adjust_volume"],
        )
