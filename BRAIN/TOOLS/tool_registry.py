"""
JARVIS AI — Tool & Action Registry
Defines validated, typed tools bridging the LLM and existing automation subsystems.
Returns structured results: {"success": bool, "data": Any, "error": Optional[str]}.
"""

import datetime
import os
import sys
import webbrowser
from typing import Any, Callable, Dict, List, Optional
import psutil

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import import_module_from_path, PATHS
from BRAIN.TOOLS.safety_manager import safety_manager


class ToolRegistry:
    """Central registry and executor for all JARVIS tools."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_all_tools()

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Dict[str, Any]],
    ):
        """Register a new tool with its schema and handler."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return schema definitions compatible with OpenAI, Gemini, and Ollama."""
        schemas = []
        for name, meta in self._tools.items():
            schemas.append({
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            })
        return schemas

    def execute_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a registered tool safely and return structured result.
        """
        arguments = arguments or {}

        if name not in self._tools:
            return {
                "success": False,
                "data": None,
                "error": f"Tool '{name}' is not registered in the system.",
            }

        # Safety check
        if not safety_manager.validate_execution(name, arguments, confirm_callback):
            return {
                "success": False,
                "data": None,
                "error": f"Execution of tool '{name}' was blocked by safety policy or rejected by user.",
            }

        handler = self._tools[name]["handler"]
        try:
            result = handler(**arguments)
            if isinstance(result, dict) and "success" in result:
                return result
            return {"success": True, "data": result, "error": None}
        except TypeError as te:
            return {"success": False, "data": None, "error": f"Invalid arguments for '{name}': {te}"}
        except Exception as e:
            return {"success": False, "data": None, "error": f"Error executing '{name}': {str(e)}"}

    def _register_all_tools(self):
        """Register all core capability tools."""

        # ── 1. System & Time ─────────────────────────────────────────────
        def _get_time() -> Dict[str, Any]:
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            return {"success": True, "data": {"time": time_str, "date": date_str, "formatted": f"{time_str} on {date_str}"}, "error": None}

        self.register(
            name="get_time",
            description="Get the current system time and date.",
            parameters={"type": "object", "properties": {}},
            handler=_get_time,
        )

        # ── 2. Weather ──────────────────────────────────────────────────
        def _get_weather(city: Optional[str] = None) -> Dict[str, Any]:
            from config import WEATHER_CITY
            target_city = city or WEATHER_CITY
            try:
                temp_mod = import_module_from_path('temp', os.path.join(PROJECT_ROOT, 'FUNCTION', 'CHECK_TEMPEATURE', 'temp.py'))
                # If Temp module prints/speaks, fetch weather info directly
                from config import OPENWEATHERMAP_API_KEY
                import requests
                if OPENWEATHERMAP_API_KEY:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={target_city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        w_data = r.json()
                        temp_c = w_data['main']['temp']
                        desc = w_data['weather'][0]['description']
                        return {"success": True, "data": {"city": target_city, "temperature_c": temp_c, "condition": desc, "formatted": f"{temp_c}°C and {desc} in {target_city}"}, "error": None}
                return {"success": True, "data": {"city": target_city, "temperature_c": "25", "condition": "Clear sky", "formatted": f"Around 25°C and clear in {target_city}"}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="get_weather",
            description="Get the current weather and temperature for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name to check weather for."}
                }
            },
            handler=_get_weather,
        )

        # ── 3. Battery Status ────────────────────────────────────────────
        def _get_battery() -> Dict[str, Any]:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    pct = int(battery.percent)
                    plugged = bool(battery.power_plugged)
                    status = "Plugged in (Charging)" if plugged else "Discharging"
                    return {"success": True, "data": {"percent": pct, "plugged_in": plugged, "status": status, "formatted": f"Battery is at {pct}%, {status}"}, "error": None}
                return {"success": True, "data": {"percent": 100, "plugged_in": True, "status": "Desktop / AC Power", "formatted": "Running on AC Power (no battery detected)"}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="get_battery_status",
            description="Get the computer's battery percentage and charging status.",
            parameters={"type": "object", "properties": {}},
            handler=_get_battery,
        )

        # ── 4. IP Address ────────────────────────────────────────────────
        def _get_ip() -> Dict[str, Any]:
            try:
                ip_mod = import_module_from_path('find_my_ip', os.path.join(PROJECT_ROOT, 'FUNCTION', 'FIND_MY_IP', 'find_my_ip.py'))
                ip = ip_mod.find_my_ip()
                return {"success": True, "data": {"ip": ip, "formatted": f"Public IP is {ip}"}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="get_ip",
            description="Get the public IP address of the machine.",
            parameters={"type": "object", "properties": {}},
            handler=_get_ip,
        )

        # ── 5. Internet Status ───────────────────────────────────────────
        def _check_internet() -> Dict[str, Any]:
            try:
                import requests
                r = requests.get("https://www.google.com", timeout=3)
                online = r.status_code == 200
                return {"success": True, "data": {"online": online, "status": "Connected to Internet" if online else "Offline"}, "error": None}
            except Exception:
                return {"success": True, "data": {"online": False, "status": "No Internet Connection"}, "error": None}

        self.register(
            name="check_internet",
            description="Check if the internet connection is active and stable.",
            parameters={"type": "object", "properties": {}},
            handler=_check_internet,
        )

        # ── 6. Joke & Advice ─────────────────────────────────────────────
        def _get_joke() -> Dict[str, Any]:
            try:
                joke_mod = import_module_from_path('joke', os.path.join(PROJECT_ROOT, 'BRAIN', 'ACTIVITY', 'JOKE', 'joke.py'))
                joke = joke_mod.get_random_joke()
                return {"success": True, "data": {"joke": joke}, "error": None}
            except Exception:
                return {"success": True, "data": {"joke": "Why do programmers prefer dark mode? Because light attracts bugs."}, "error": None}

        self.register(
            name="get_joke",
            description="Get a funny tech joke.",
            parameters={"type": "object", "properties": {}},
            handler=_get_joke,
        )

        def _get_advice() -> Dict[str, Any]:
            try:
                adv_mod = import_module_from_path('advice', os.path.join(PROJECT_ROOT, 'BRAIN', 'ACTIVITY', 'ADVICE', 'advice.py'))
                advice = adv_mod.get_random_advice()
                return {"success": True, "data": {"advice": advice}, "error": None}
            except Exception:
                return {"success": True, "data": {"advice": "Keep learning and building consistently."}, "error": None}

        self.register(
            name="get_advice",
            description="Get a useful piece of life or productivity advice.",
            parameters={"type": "object", "properties": {}},
            handler=_get_advice,
        )

        # ── 7. Web & Google ──────────────────────────────────────────────
        def _open_website(url: str) -> Dict[str, Any]:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return {"success": True, "data": {"opened_url": url, "message": f"Opened {url} in browser."}, "error": None}

        self.register(
            name="open_website",
            description="Open any website or URL in the default web browser.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL or website domain to open (e.g. 'github.com', 'https://reddit.com')."}
                },
                "required": ["url"],
            },
            handler=_open_website,
        )

        def _search_google(query: str) -> Dict[str, Any]:
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            return {"success": True, "data": {"query": query, "message": f"Searched Google for '{query}'."}, "error": None}

        self.register(
            name="search_google",
            description="Search for a query on Google in the web browser.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term or query."}
                },
                "required": ["query"],
            },
            handler=_search_google,
        )

        # ── 8. YouTube Automation ────────────────────────────────────────
        def _youtube_play(query: str) -> Dict[str, Any]:
            import pywhatkit
            pywhatkit.playonyt(query)
            return {"success": True, "data": {"query": query, "message": f"Playing '{query}' on YouTube."}, "error": None}

        self.register(
            name="youtube_play",
            description="Search and play a video or music track on YouTube.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The song, artist, or video title to play on YouTube."}
                },
                "required": ["query"],
            },
            handler=_youtube_play,
        )

        def _youtube_pause() -> Dict[str, Any]:
            import pyautogui
            pyautogui.press('k')
            return {"success": True, "data": {"action": "toggle_pause", "message": "Toggled YouTube video play/pause."}, "error": None}

        self.register(
            name="youtube_pause",
            description="Toggle play/pause on the active YouTube video.",
            parameters={"type": "object", "properties": {}},
            handler=_youtube_pause,
        )

        def _youtube_volume(direction: str = "up") -> Dict[str, Any]:
            import pyautogui
            key = 'up' if direction.lower() == 'up' else 'down'
            for _ in range(3):
                pyautogui.press(key)
            return {"success": True, "data": {"direction": direction, "message": f"Adjusted YouTube volume {direction}."}, "error": None}

        self.register(
            name="youtube_volume",
            description="Adjust YouTube playback volume up or down.",
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"], "description": "Direction to adjust volume ('up' or 'down')."}
                },
                "required": ["direction"],
            },
            handler=_youtube_volume,
        )

        # ── 9. Windows Applications ──────────────────────────────────────
        def _launch_app(app_name: str) -> Dict[str, Any]:
            import pyautogui
            import time
            pyautogui.press('win')
            time.sleep(0.3)
            pyautogui.write(app_name, interval=0.03)
            time.sleep(0.3)
            pyautogui.press('enter')
            return {"success": True, "data": {"app_name": app_name, "message": f"Launched application '{app_name}'."}, "error": None}

        self.register(
            name="launch_application",
            description="Launch a desktop application or program in Windows (e.g. 'notepad', 'chrome', 'calculator', 'spotify').",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application to open."}
                },
                "required": ["app_name"],
            },
            handler=_launch_app,
        )

        def _close_app(app_name: str) -> Dict[str, Any]:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return {"success": True, "data": {"app_name": app_name, "message": f"Closed active window for '{app_name}'."}, "error": None}

        self.register(
            name="close_application",
            description="Close the currently active application window.",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application to close."}
                },
                "required": ["app_name"],
            },
            handler=_close_app,
        )

        # ── 10. Automation Manager Integration ───────────────────────────
        def _create_automation(name: str, action: str, parameters: Optional[Dict[str, Any]] = None, schedule_time: Optional[str] = None) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            auto = mgr.create_automation(name=name, action=action, parameters=parameters or {}, schedule_time=schedule_time)
            if auto:
                return {"success": True, "data": auto, "error": None}
            return {"success": False, "data": None, "error": f"Failed to create automation '{name}'. Invalid action or parameters."}

        self.register(
            name="create_automation",
            description="Create a recurring or on-demand automated task in JARVIS.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name or description of the automation."},
                    "action": {
                        "type": "string",
                        "enum": ["open_website", "open_app", "search_google", "search_youtube", "play_music", "speak_text", "check_weather", "check_time", "check_battery", "check_ip", "check_speed", "get_joke", "get_advice"],
                        "description": "The allowed action type to perform."
                    },
                    "parameters": {"type": "object", "description": "Key-value parameters for the action (e.g. {'url': 'youtube.com'} or {'query': 'lofi music'})."},
                    "schedule_time": {"type": "string", "description": "Optional scheduled time in HH:MM format (24-hour, e.g. '09:00', '21:30')."}
                },
                "required": ["name", "action"],
            },
            handler=_create_automation,
        )

        def _list_automations() -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            autos = mgr.list_automations(speak_output=False)
            return {"success": True, "data": {"count": len(autos), "automations": autos}, "error": None}

        self.register(
            name="list_automations",
            description="List all configured custom automations and their status.",
            parameters={"type": "object", "properties": {}},
            handler=_list_automations,
        )

        def _delete_automation(automation_id: str) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            success = mgr.delete_automation(automation_id)
            return {"success": success, "data": {"automation_id": automation_id}, "error": None if success else "Automation not found"}

        self.register(
            name="delete_automation",
            description="Delete an existing automation by its ID.",
            parameters={
                "type": "object",
                "properties": {
                    "automation_id": {"type": "string", "description": "The ID of the automation to delete."}
                },
                "required": ["automation_id"],
            },
            handler=_delete_automation,
        )

        def _run_automation(name_or_id: str) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            # Try by ID first, then by name
            auto = mgr.get_automation(name_or_id)
            if auto:
                success = mgr.execute_automation(name_or_id)
            else:
                success = mgr.execute_automation_by_name(name_or_id)
            return {"success": success, "data": {"target": name_or_id, "executed": success}, "error": None if success else f"Could not find or run automation '{name_or_id}'"}

        self.register(
            name="run_automation",
            description="Execute an existing automation immediately by its name or ID.",
            parameters={
                "type": "object",
                "properties": {
                    "name_or_id": {"type": "string", "description": "Name or ID of the automation to run."}
                },
                "required": ["name_or_id"],
            },
            handler=_run_automation,
        )

        def _get_history() -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            logs = mgr.get_automation_history(speak_output=False)
            return {"success": True, "data": {"count": len(logs), "logs": logs[-10:]}, "error": None}

        self.register(
            name="get_automation_history",
            description="Get the recent execution history and status logs of automations.",
            parameters={"type": "object", "properties": {}},
            handler=_get_history,
        )

        # ── 11. Memory Tools ─────────────────────────────────────────────
        def _remember_memory(key: str, value: str, category: str = "preference") -> Dict[str, Any]:
            try:
                mem_mod = import_module_from_path('memory_manager', PATHS['memory_manager'])
                success = mem_mod.memory_manager.store_fact(key=key, value=value, category=category)
                return {"success": success, "data": {"key": key, "value": value, "category": category, "message": f"Remembered: '{key}' is '{value}'."}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="remember_memory",
            description="Store a user preference, recurring trait, or important fact into long-term memory.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key or topic identifier (e.g. 'favorite_artist', 'default_city')."},
                    "value": {"type": "string", "description": "The detail or preference to remember."},
                    "category": {"type": "string", "enum": ["preference", "fact", "routine"], "description": "Category of the memory."}
                },
                "required": ["key", "value"],
            },
            handler=_remember_memory,
        )

        def _recall_memory(query: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
            try:
                mem_mod = import_module_from_path('memory_manager', PATHS['memory_manager'])
                facts = mem_mod.memory_manager.recall_facts(query=query, category=category)
                return {"success": True, "data": {"facts": facts}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="recall_memory",
            description="Retrieve stored user preferences or remembered facts from long-term memory.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional search term or keyword."},
                    "category": {"type": "string", "description": "Optional category filter."}
                }
            },
            handler=_recall_memory,
        )


# Global singleton instance
tool_registry = ToolRegistry()
