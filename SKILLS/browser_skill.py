"""
JARVIS AI — Browser Skill Module
Encapsulates web browsing and Google search tools.
"""

import webbrowser
from typing import Any, Dict
from SKILLS.base_skill import BaseSkill, SkillCategory


class BrowserSkill(BaseSkill):
    """Provides web browser launching and web searching capabilities."""

    def __init__(self):
        super().__init__(
            name="browser",
            description="Opens websites and executes web searches in the browser.",
            category=SkillCategory.WEB,
        )

    def initialize(self):
        def _open_website(url: str) -> Dict[str, Any]:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return {"success": True, "data": {"opened_url": url, "message": f"Opened {url} in browser."}, "error": None}

        self.register_tool(
            name="browser.open",
            description="Open any website or URL in the default web browser.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL or domain to open (e.g. 'github.com', 'https://reddit.com')."}
                },
                "required": ["url"],
            },
            handler=_open_website,
            risk_level="low",
            aliases=["open_website", "web.open"],
        )

        def _search_google(query: str) -> Dict[str, Any]:
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            return {"success": True, "data": {"query": query, "message": f"Searched Google for '{query}'."}, "error": None}

        self.register_tool(
            name="browser.search",
            description="Search for a query on Google in the web browser.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term or query."}
                },
                "required": ["query"],
            },
            handler=_search_google,
            risk_level="low",
            aliases=["search_google", "google.search"],
        )
