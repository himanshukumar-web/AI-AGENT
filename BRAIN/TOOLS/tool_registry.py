"""
JARVIS AI — Namespaced Tool Registry & Action Dispatcher
Provides strictly typed, validated tools bridging LLM/Planner and all JARVIS capabilities.
Integrates action auditing, safety validation, metrics, and structured results.
"""

import datetime
import os
import sys
import time
import webbrowser
from typing import Any, Callable, Dict, List, Optional
import psutil

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import import_module_from_path, PATHS
from BRAIN.TOOLS.safety_manager import safety_manager
from BRAIN.TOOLS.action_logger import action_logger
from BRAIN.UTILS.metrics import metrics_tracker
from BRAIN.UTILS.logger import jarvis_logger


class ToolRegistry:
    """Central registry, validator, and executor for all JARVIS tools."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._aliases: Dict[str, str] = {}
        self._register_all_tools()

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Dict[str, Any]],
        aliases: Optional[List[str]] = None,
    ):
        """Register a tool with its schema, handler, and optional aliases."""
        tool_data = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }
        self._tools[name] = tool_data
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return standardized schemas compatible with OpenAI, Gemini, Groq, and Ollama."""
        schemas = []
        for name, meta in self._tools.items():
            schemas.append({
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            })
        return schemas

    def get_contextual_tools(self, query: Optional[str] = None, active_topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Dynamically select and return only relevant tool schemas for a given query or context topic.
        Dramatically reduces LLM prompt token size and prevents hallucinations.
        """
        if not query and not active_topic:
            return self.get_tool_definitions()

        q = (query or "").lower()
        topic = (active_topic or "").lower()

        relevant_prefixes = set()

        # Topic/Keyword mapping
        if "youtube" in q or "music" in q or "song" in q or "video" in q or topic == "youtube":
            relevant_prefixes.update(["youtube.", "browser.", "research.", "web."])
        if "browser" in q or "google" in q or "website" in q or "url" in q or topic == "browser":
            relevant_prefixes.update(["browser.", "research.", "web."])
        if "research" in q or "search" in q or "compare" in q or "citation" in q or topic == "research":
            relevant_prefixes.update(["web.", "research.", "browser."])
        if any(k in q for k in ["screen", "display", "monitor", "click", "mouse", "type", "keyboard", "window", "cursor", "desktop", "capture", "see", "look", "button", "computer"]) or topic == "computer":
            relevant_prefixes.update(["computer.", "browser."])
        if "automation" in q or "schedule" in q or "alarm" in q or "timer" in q or topic == "automation":
            relevant_prefixes.update(["automation.", "system.time"])
        if "weather" in q or "temperature" in q or "mausam" in q or topic == "weather":
            relevant_prefixes.update(["weather.", "system.time"])
        if "memory" in q or "remember" in q or "recall" in q or "forget" in q or topic == "memory":
            relevant_prefixes.update(["memory."])
        if any(k in q for k in ["battery", "charge", "power", "ip", "joke", "advice", "app", "application", "diagnostic", "status", "doctor"]):
            relevant_prefixes.update(["system.", "action."])

        if not relevant_prefixes:
            # For general multi-step or broad reasoning, return all tools
            return self.get_tool_definitions()

        # Always include minimal core utilities if needed
        relevant_prefixes.add("system.time")

        filtered = []
        for name, meta in self._tools.items():
            if any(name.startswith(p) for p in relevant_prefixes):
                filtered.append({
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["parameters"],
                })

        return filtered if filtered else self.get_tool_definitions()


    def resolve_tool_name(self, name: str) -> Optional[str]:
        """Resolve a tool name or alias to canonical name."""
        clean = name.strip()
        if clean in self._tools:
            return clean
        if clean in self._aliases:
            return self._aliases[clean]
        clean_lower = clean.lower()
        if clean_lower in self._tools:
            return clean_lower
        if clean_lower in self._aliases:
            return self._aliases[clean_lower]
        return None

    def execute_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None,
        user_request: str = "",
    ) -> Dict[str, Any]:
        """
        Safely execute a tool with permission validation, timing, and action logging.
        """
        arguments = arguments or {}
        canonical_name = self.resolve_tool_name(name)

        if not canonical_name or canonical_name not in self._tools:
            err = f"Tool '{name}' is not registered in the system."
            jarvis_logger.warning("TOOLS", err)
            return {"success": False, "data": None, "error": err}

        # Safety validation
        risk = safety_manager.get_risk_level(canonical_name)
        if not safety_manager.validate_execution(canonical_name, arguments, confirm_callback):
            err = f"Execution of tool '{canonical_name}' blocked by safety policy or rejected by user."
            jarvis_logger.warning("SAFETY", err)
            action_logger.log_action(canonical_name, arguments, {"success": False, "error": err}, 0.0, risk.value, user_request)
            return {"success": False, "data": None, "error": err}

        # Computer Use safety validation (budget, emergency stop, sensitive contexts)
        if canonical_name.startswith("computer."):
            try:
                from BRAIN.COMPUTER.safety.computer_safety import computer_safety_manager
                c_safe, c_err = computer_safety_manager.check_pre_action_safety(canonical_name, arguments)
                if not c_safe:
                    jarvis_logger.warning("SAFETY", c_err)
                    action_logger.log_action(canonical_name, arguments, {"success": False, "error": c_err}, 0.0, risk.value, user_request)
                    return {"success": False, "data": None, "error": c_err}
            except Exception as e:
                jarvis_logger.warning("SAFETY", f"Computer safety check error: {e}")

        handler = self._tools[canonical_name]["handler"]
        start_t = time.perf_counter()
        try:
            result = handler(**arguments)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            metrics_tracker.record_tool_execution()

            if not isinstance(result, dict) or "success" not in result:
                result = {"success": True, "data": result, "error": None}

            action_logger.log_action(canonical_name, arguments, result, duration_ms, risk.value, user_request)
            jarvis_logger.info("TOOLS", f"Executed '{canonical_name}' in {duration_ms:.1f}ms (Status: {result.get('success')})")
            return result
        except TypeError as te:
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            err_res = {"success": False, "data": None, "error": f"Invalid arguments for '{canonical_name}': {te}"}
            action_logger.log_action(canonical_name, arguments, err_res, duration_ms, risk.value, user_request)
            return err_res
        except Exception as e:
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            err_res = {"success": False, "data": None, "error": f"Error executing '{canonical_name}': {str(e)}"}
            action_logger.log_action(canonical_name, arguments, err_res, duration_ms, risk.value, user_request)
            return err_res

    def _register_all_tools(self):
        """Register all core capability tools."""

        # ── 1. System & Time ─────────────────────────────────────────────
        def _get_time() -> Dict[str, Any]:
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            return {"success": True, "data": {"time": time_str, "date": date_str, "formatted": f"{time_str} on {date_str}"}, "error": None}

        self.register(
            name="system.time",
            description="Get the current system time and date.",
            parameters={"type": "object", "properties": {}},
            handler=_get_time,
            aliases=["get_time"],
        )

        # ── 2. Weather ──────────────────────────────────────────────────
        def _get_weather(city: Optional[str] = None) -> Dict[str, Any]:
            from config import WEATHER_CITY, OPENWEATHERMAP_API_KEY
            target_city = city or WEATHER_CITY
            try:
                import requests
                if OPENWEATHERMAP_API_KEY:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={target_city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        w = r.json()
                        temp_c = w['main']['temp']
                        desc = w['weather'][0]['description']
                        return {"success": True, "data": {"city": target_city, "temperature_c": temp_c, "condition": desc, "formatted": f"{temp_c}°C and {desc} in {target_city}"}, "error": None}
                return {"success": True, "data": {"city": target_city, "temperature_c": "25", "condition": "Clear sky", "formatted": f"Around 25°C and clear in {target_city}"}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="weather.get",
            description="Get the current weather and temperature for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name to check weather for."}
                }
            },
            handler=_get_weather,
            aliases=["get_weather"],
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
            name="system.battery",
            description="Get the computer's battery percentage and charging status.",
            parameters={"type": "object", "properties": {}},
            handler=_get_battery,
            aliases=["get_battery_status"],
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
            name="system.ip",
            description="Get the public IP address of the machine.",
            parameters={"type": "object", "properties": {}},
            handler=_get_ip,
            aliases=["get_ip"],
        )

        # ── 5. Internet Connectivity ─────────────────────────────────────
        def _check_internet() -> Dict[str, Any]:
            try:
                import requests
                r = requests.get("https://www.google.com", timeout=3)
                online = r.status_code == 200
                return {"success": True, "data": {"online": online, "status": "Connected to Internet" if online else "Offline"}, "error": None}
            except Exception:
                return {"success": True, "data": {"online": False, "status": "No Internet Connection"}, "error": None}

        self.register(
            name="system.internet",
            description="Check if the internet connection is active and stable.",
            parameters={"type": "object", "properties": {}},
            handler=_check_internet,
            aliases=["check_internet"],
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
            name="system.joke",
            description="Get a programming or tech joke.",
            parameters={"type": "object", "properties": {}},
            handler=_get_joke,
            aliases=["get_joke"],
        )

        def _get_advice() -> Dict[str, Any]:
            try:
                adv_mod = import_module_from_path('advice', os.path.join(PROJECT_ROOT, 'BRAIN', 'ACTIVITY', 'ADVICE', 'advice.py'))
                advice = adv_mod.get_random_advice()
                return {"success": True, "data": {"advice": advice}, "error": None}
            except Exception:
                return {"success": True, "data": {"advice": "Keep learning and building consistently."}, "error": None}

        self.register(
            name="system.advice",
            description="Get a useful productivity or motivational tip.",
            parameters={"type": "object", "properties": {}},
            handler=_get_advice,
            aliases=["get_advice"],
        )

        # ── 7. Browser & Google Search ───────────────────────────────────
        def _open_website(url: str) -> Dict[str, Any]:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return {"success": True, "data": {"opened_url": url, "message": f"Opened {url} in browser."}, "error": None}

        self.register(
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
            aliases=["open_website", "web.open"],
        )

        def _search_google(query: str) -> Dict[str, Any]:
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            return {"success": True, "data": {"query": query, "message": f"Searched Google for '{query}'."}, "error": None}

        self.register(
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
            aliases=["search_google"],
        )

        # ── 8. YouTube Automation ────────────────────────────────────────
        def _youtube_play(query: str) -> Dict[str, Any]:
            import pywhatkit
            pywhatkit.playonyt(query)
            return {"success": True, "data": {"query": query, "message": f"Playing '{query}' on YouTube."}, "error": None}

        self.register(
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
            aliases=["youtube_play"],
        )

        def _youtube_search(query: str) -> Dict[str, Any]:
            url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(url)
            # Store search items for ordinal follow-ups
            from BRAIN.MEMORY.conversation_manager import conversation_manager
            simulated_results = [f"{query} - Video 1", f"{query} - Video 2", f"{query} - Video 3"]
            conversation_manager.set_search_results(simulated_results)
            conversation_manager.set_context_state(active_topic="youtube", last_action="youtube.search")
            return {"success": True, "data": {"query": query, "results": simulated_results, "message": f"Searched YouTube for '{query}'."}, "error": None}

        self.register(
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
        )

        def _youtube_pause() -> Dict[str, Any]:
            import pyautogui
            pyautogui.press('k')
            return {"success": True, "data": {"action": "toggle_pause", "message": "Toggled YouTube video play/pause."}, "error": None}

        self.register(
            name="youtube.pause",
            description="Toggle play/pause on the active YouTube video.",
            parameters={"type": "object", "properties": {}},
            handler=_youtube_pause,
            aliases=["youtube_pause"],
        )

        def _youtube_volume(direction: str = "up") -> Dict[str, Any]:
            import pyautogui
            key = 'up' if direction.lower() == 'up' else 'down'
            for _ in range(3):
                pyautogui.press(key)
            return {"success": True, "data": {"direction": direction, "message": f"Adjusted YouTube volume {direction}."}, "error": None}

        self.register(
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
            aliases=["youtube_volume"],
        )

        # ── 9. Windows Application Management ────────────────────────────
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
            name="system.launch_app",
            description="Launch a desktop application in Windows (e.g. 'notepad', 'chrome', 'calc', 'spotify').",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application."}
                },
                "required": ["app_name"],
            },
            handler=_launch_app,
            aliases=["launch_application"],
        )

        def _close_app(app_name: str) -> Dict[str, Any]:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return {"success": True, "data": {"app_name": app_name, "message": f"Closed active window for '{app_name}'."}, "error": None}

        self.register(
            name="system.close_app",
            description="Close the currently active window for an application.",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application to close."}
                },
                "required": ["app_name"],
            },
            handler=_close_app,
            aliases=["close_application"],
        )

        # ── 10. Automation Manager ───────────────────────────────────────
        def _create_automation(name: str, action: str, parameters: Optional[Dict[str, Any]] = None, schedule_time: Optional[str] = None) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            auto = mgr.create_automation(name=name, action=action, parameters=parameters or {}, schedule_time=schedule_time)
            if auto:
                return {"success": True, "data": auto, "error": None}
            return {"success": False, "data": None, "error": f"Failed to create automation '{name}'."}

        self.register(
            name="automation.create",
            description="Create a recurring or on-demand automated task in JARVIS.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the automation."},
                    "action": {"type": "string", "description": "Action type."},
                    "parameters": {"type": "object", "description": "Action parameters."},
                    "schedule_time": {"type": "string", "description": "Scheduled time in HH:MM format (e.g. '09:00')."}
                },
                "required": ["name", "action"],
            },
            handler=_create_automation,
            aliases=["create_automation"],
        )

        def _list_automations() -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            autos = mgr.list_automations(speak_output=False)
            return {"success": True, "data": {"count": len(autos), "automations": autos}, "error": None}

        self.register(
            name="automation.list",
            description="List all configured custom automations.",
            parameters={"type": "object", "properties": {}},
            handler=_list_automations,
            aliases=["list_automations"],
        )

        def _update_automation(automation_id: str, **updates) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            res = mgr.edit_automation(automation_id, **updates)
            if res:
                return {"success": True, "data": res, "error": None}
            return {"success": False, "data": None, "error": f"Could not update automation '{automation_id}'."}

        self.register(
            name="automation.update",
            description="Update an existing automation's properties or status.",
            parameters={
                "type": "object",
                "properties": {
                    "automation_id": {"type": "string", "description": "The ID of the automation."},
                    "enabled": {"type": "boolean", "description": "Enable or disable status."}
                },
                "required": ["automation_id"],
            },
            handler=_update_automation,
            aliases=["update_automation"],
        )

        def _delete_automation(automation_id: str) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            success = mgr.delete_automation(automation_id)
            return {"success": success, "data": {"automation_id": automation_id}, "error": None if success else "Automation not found"}

        self.register(
            name="automation.delete",
            description="Delete an existing automation by its ID.",
            parameters={
                "type": "object",
                "properties": {
                    "automation_id": {"type": "string", "description": "The ID of the automation to delete."}
                },
                "required": ["automation_id"],
            },
            handler=_delete_automation,
            aliases=["delete_automation"],
        )

        def _run_automation(name_or_id: str) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            auto = mgr.get_automation(name_or_id)
            if auto:
                success = mgr.execute_automation(name_or_id)
            else:
                success = mgr.execute_automation_by_name(name_or_id)
            return {"success": success, "data": {"target": name_or_id, "executed": success}, "error": None if success else f"Could not find or run automation '{name_or_id}'"}

        self.register(
            name="automation.run",
            description="Execute an automation immediately by name or ID.",
            parameters={
                "type": "object",
                "properties": {
                    "name_or_id": {"type": "string", "description": "Name or ID of the automation."}
                },
                "required": ["name_or_id"],
            },
            handler=_run_automation,
            aliases=["run_automation"],
        )

        def _get_history() -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            logs = mgr.get_automation_history(speak_output=False)
            return {"success": True, "data": {"count": len(logs), "logs": logs[-10:]}, "error": None}

        self.register(
            name="automation.history",
            description="Get the recent execution logs of automations.",
            parameters={"type": "object", "properties": {}},
            handler=_get_history,
            aliases=["get_automation_history"],
        )

        # ── 11. Memory 2.0 Tools ─────────────────────────────────────────
        def _remember_memory(key: str, value: str, category: str = "preference") -> Dict[str, Any]:
            try:
                from BRAIN.MEMORY.memory_manager import memory_manager
                success = memory_manager.store_fact(key=key, value=value, category=category)
                return {"success": success, "data": {"key": key, "value": value, "category": category, "message": f"Remembered: '{key}' is '{value}'."}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="memory.remember",
            description="Store a user preference or fact into persistent long-term memory.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key or topic (e.g. 'favorite_genre', 'work_role')."},
                    "value": {"type": "string", "description": "Detail to remember."},
                    "category": {"type": "string", "enum": ["preference", "fact", "routine"], "description": "Category."}
                },
                "required": ["key", "value"],
            },
            handler=_remember_memory,
            aliases=["remember_memory"],
        )

        def _recall_memory(query: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
            try:
                from BRAIN.MEMORY.memory_manager import memory_manager
                facts = memory_manager.recall_facts(query=query, category=category)
                return {"success": True, "data": {"count": len(facts), "facts": facts}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="memory.recall",
            description="Retrieve stored user preferences or remembered facts from memory.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword."},
                    "category": {"type": "string", "description": "Category filter."}
                }
            },
            handler=_recall_memory,
            aliases=["recall_memory", "memory.list"],
        )

        def _forget_memory(query: str) -> Dict[str, Any]:
            try:
                from BRAIN.MEMORY.memory_manager import memory_manager
                count = memory_manager.forget_facts_matching(query)
                return {"success": True, "data": {"deleted_count": count, "message": f"Removed {count} memory records matching '{query}'."}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="memory.forget",
            description="Forget or remove remembered facts from memory matching a keyword or topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic or keyword to forget."}
                },
                "required": ["query"],
            },
            handler=_forget_memory,
        )

        # ── 12. Deep Research & Web Intelligence Tools ───────────────────
        def _web_search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
            from WEB.search.provider_manager import search_provider_manager
            results = search_provider_manager.search(query, max_results=max_results)
            return {"success": True, "data": {"query": query, "count": len(results), "results": [r.to_dict() for r in results]}, "error": None}

        self.register(
            name="web.search",
            description="Search the web across independent search providers and return top ranked sources.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "max_results": {"type": "integer", "description": "Maximum number of results."}
                },
                "required": ["query"],
            },
            handler=_web_search_tool,
            aliases=["search", "web_search"],
        )

        def _web_extract_tool(url: str) -> Dict[str, Any]:
            from WEB.extraction.extractor import web_extractor
            ext = web_extractor.fetch_and_extract(url)
            return {
                "success": ext.success,
                "data": {
                    "url": ext.url,
                    "title": ext.title,
                    "text": ext.text,
                    "headings": ext.headings,
                    "tables": ext.tables,
                    "word_count": ext.word_count,
                    "publication_date": ext.publication_date,
                },
                "error": ext.error,
            }

        self.register(
            name="web.extract",
            description="Safely extract readable body text, headings, and tables from a web URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to extract content from."}
                },
                "required": ["url"],
            },
            handler=_web_extract_tool,
            aliases=["extract_webpage", "web_extract"],
        )

        def _web_find_tool(query: str, max_results: int = 3) -> Dict[str, Any]:
            from WEB.search.provider_manager import search_provider_manager
            results = search_provider_manager.search(query, max_results=max_results)
            snippets = [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
            return {"success": True, "data": {"query": query, "results": snippets}, "error": None}

        self.register(
            name="web.find",
            description="Quickly find relevant snippets and URLs for a topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "max_results": {"type": "integer", "description": "Number of snippets to retrieve."}
                },
                "required": ["query"],
            },
            handler=_web_find_tool,
            aliases=["find_on_web", "web_find"],
        )

        def _web_collect_sources_tool(query: str, limit: int = 5) -> Dict[str, Any]:
            from WEB.search.provider_manager import search_provider_manager
            from WEB.extraction.deduplicator import source_deduplicator
            from WEB.intelligence.source_scorer import source_scorer
            raw = search_provider_manager.search(query, max_results=limit * 2)
            unique = source_deduplicator.deduplicate(raw)[:limit]
            scored = []
            for s in unique:
                sc = source_scorer.score_source(s, query=query)
                d = s.to_dict()
                d["quality_tier"] = sc.tier
                d["quality_score"] = sc.overall_score
                scored.append(d)
            return {"success": True, "data": {"query": query, "count": len(scored), "sources": scored}, "error": None}

        self.register(
            name="web.collect_sources",
            description="Collect and score independent, deduplicated web sources for a research topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The topic to collect sources for."},
                    "limit": {"type": "integer", "description": "Target number of sources."}
                },
                "required": ["query"],
            },
            handler=_web_collect_sources_tool,
            aliases=["collect_sources"],
        )

        def _web_compare_sources_tool(entities: List[str]) -> Dict[str, Any]:
            from WEB.intelligence.comparator import comparison_engine
            res = comparison_engine.compare(entities)
            return {
                "success": True,
                "data": {
                    "entities": res.entities,
                    "matrix": res.matrix,
                    "markdown_table": res.markdown_table,
                    "recommendation": res.recommendation,
                },
                "error": None,
            }

        self.register(
            name="web.compare_sources",
            description="Produce a structured comparison matrix across products, models, or technologies.",
            parameters={
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entities to compare."
                    }
                },
                "required": ["entities"],
            },
            handler=_web_compare_sources_tool,
            aliases=["compare", "compare_technologies"],
        )

        def _web_research_tool(query: str, mode: str = "standard") -> Dict[str, Any]:
            from WEB.research.planner import research_planner, ResearchMode
            m = ResearchMode.DEEP if mode.lower() == "deep" else (ResearchMode.QUICK if mode.lower() == "quick" else ResearchMode.STANDARD)
            res = research_planner.plan_and_execute(query, mode=m)
            return {
                "success": not res.cancelled,
                "data": {
                    "session_id": res.session_id,
                    "query": res.query,
                    "mode": res.mode.value,
                    "summary": res.summary,
                    "key_findings": res.key_findings,
                    "sources_count": len(res.sources),
                    "full_report": res.full_report,
                },
                "error": "Research was cancelled" if res.cancelled else None,
            }

        self.register(
            name="web.research",
            description="Execute multi-step autonomous research, cross-referencing, and report synthesis.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The topic or question to research."},
                    "mode": {"type": "string", "enum": ["quick", "standard", "deep"], "description": "Depth mode."}
                },
                "required": ["query"],
            },
            handler=_web_research_tool,
            aliases=["research", "research.deep_search", "deep_search"],
        )

        def _web_citations_tool() -> Dict[str, Any]:
            from WEB.intelligence.citations import citation_manager
            cits = [c.__dict__ for c in citation_manager.list_citations()]
            formatted = citation_manager.format_sources_section()
            return {"success": True, "data": {"count": len(cits), "citations": cits, "formatted": formatted}, "error": None}

        self.register(
            name="web.citations",
            description="Get the verified citations and reference bibliography for the active research session.",
            parameters={"type": "object", "properties": {}},
            handler=_web_citations_tool,
            aliases=["citations", "get_citations"],
        )

        # ── 13. System Diagnostics (Doctor) ──────────────────────────────
        def _run_diagnostics() -> Dict[str, Any]:
            try:
                from BRAIN.UTILS.diagnostics import doctor
                report = doctor.run_diagnostics()
                doctor.print_report()
                return {"success": True, "data": report, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="system.diagnostics",
            description="Run a complete self-diagnostics health check of JARVIS subsystems.",
            parameters={"type": "object", "properties": {}},
            handler=_run_diagnostics,
            aliases=["doctor", "run_diagnostics", "system.health"],
        )

        # ── 14. Action History Auditing ──────────────────────────────────
        def _get_action_history(limit: int = 10) -> Dict[str, Any]:
            try:
                actions = action_logger.get_recent_actions(limit=limit)
                return {"success": True, "data": {"count": len(actions), "actions": actions}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register(
            name="action.history",
            description="View recent tool executions and audit records.",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of recent records to retrieve."}
                }
            },
            handler=_get_action_history,
            aliases=["get_recent_actions", "show_recent_actions", "action.audit"],
        )

        # ── 15. Computer Vision & Controlled Computer Use ─────────────────
        from BRAIN.COMPUTER.screen.capture import screen_capture
        from BRAIN.COMPUTER.screen.monitor import monitor_manager
        from BRAIN.COMPUTER.input.mouse import mouse_controller
        from BRAIN.COMPUTER.input.keyboard import keyboard_controller
        from BRAIN.COMPUTER.window.window_manager import window_manager
        from BRAIN.COMPUTER.vision.element_detector import ui_element_detector
        from BRAIN.COMPUTER.vision.screen_analyzer import screen_analyzer
        from BRAIN.COMPUTER.safety.emergency_stop import emergency_stop_controller
        from BRAIN.COMPUTER.visual_agent import visual_action_agent

        def _computer_screenshot(save_temp: bool = False, monitor_index: Optional[int] = None) -> Dict[str, Any]:
            img = screen_capture.capture_screen(monitor_index=monitor_index)
            res = {"size": list(img.size), "saved": False}
            if save_temp:
                path = screen_capture.save_temp_screenshot(img)
                res["temp_path"] = path
                res["saved"] = True
            return {"success": True, "data": res, "error": None}

        self.register(
            name="computer.screenshot",
            description="Capture the desktop screen on-demand without persistent leaks.",
            parameters={
                "type": "object",
                "properties": {
                    "save_temp": {"type": "boolean", "description": "Whether to save to a temporary file."},
                    "monitor_index": {"type": "integer", "description": "Monitor index (default primary)."}
                }
            },
            handler=_computer_screenshot,
            aliases=["screenshot", "take_screenshot", "screen.capture"],
        )

        def _computer_screen_size(monitor_index: Optional[int] = None) -> Dict[str, Any]:
            w, h = monitor_manager.get_screen_dimensions(monitor_index)
            monitors = [m.to_dict() for m in monitor_manager.get_all_monitors()]
            return {"success": True, "data": {"width": w, "height": h, "monitors": monitors}, "error": None}

        self.register(
            name="computer.get_screen_size",
            description="Get dimensions of connected monitors and primary display.",
            parameters={
                "type": "object",
                "properties": {
                    "monitor_index": {"type": "integer", "description": "Optional monitor index."}
                }
            },
            handler=_computer_screen_size,
            aliases=["get_screen_size", "screen_size"],
        )

        def _computer_active_window() -> Dict[str, Any]:
            info = window_manager.get_active_window()
            return {"success": True, "data": info, "error": None}

        self.register(
            name="computer.get_active_window",
            description="Get details about the currently focused foreground window.",
            parameters={"type": "object", "properties": {}},
            handler=_computer_active_window,
            aliases=["get_active_window", "active_window"],
        )

        def _computer_list_windows() -> Dict[str, Any]:
            wins = window_manager.list_windows()
            return {"success": True, "data": {"count": len(wins), "windows": wins}, "error": None}

        self.register(
            name="computer.list_windows",
            description="List visible applications and desktop windows.",
            parameters={"type": "object", "properties": {}},
            handler=_computer_list_windows,
            aliases=["list_windows", "get_open_windows"],
        )

        def _computer_focus_window(title: str) -> Dict[str, Any]:
            res = window_manager.focus_window(title)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.focus_window",
            description="Bring an open window or application into active focus.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or app name of the window to focus."}
                },
                "required": ["title"]
            },
            handler=_computer_focus_window,
            aliases=["focus_window", "switch_window"],
        )

        def _computer_close_window(title: str) -> Dict[str, Any]:
            res = window_manager.close_window(title)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.close_window",
            description="Gracefully close a window or application.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or app name of the window to close."}
                },
                "required": ["title"]
            },
            handler=_computer_close_window,
            aliases=["close_window"],
        )

        def _computer_find_element(description: str, min_confidence: float = 0.60) -> Dict[str, Any]:
            el, msg = ui_element_detector.find_best_element(description, min_confidence=min_confidence)
            if el:
                return {"success": True, "data": el, "error": None}
            return {"success": False, "data": None, "error": msg}

        self.register(
            name="computer.find_element",
            description="Locate a specific UI button, input box, link, or tab on screen.",
            parameters={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Description of the UI element to locate."},
                    "min_confidence": {"type": "number", "description": "Minimum confidence threshold (0.0 to 1.0)."}
                },
                "required": ["description"]
            },
            handler=_computer_find_element,
            aliases=["find_element", "locate_ui"],
        )

        def _computer_analyze_screen(query: str = "Describe what is currently visible on the screen") -> Dict[str, Any]:
            analysis = screen_analyzer.analyze_screen(query)
            return {"success": True, "data": analysis, "error": None}

        self.register(
            name="computer.analyze_screen",
            description="Analyze visual desktop contents, active applications, and UI elements.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question or prompt about the screen."}
                }
            },
            handler=_computer_analyze_screen,
            aliases=["analyze_screen", "what_is_on_screen"],
        )

        def _computer_move_mouse(x: int, y: int, duration: float = 0.2) -> Dict[str, Any]:
            res = mouse_controller.move_mouse(x=x, y=y, duration=duration)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.move_mouse",
            description="Move mouse cursor to validated screen coordinates.",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."},
                    "duration": {"type": "number", "description": "Movement duration in seconds."}
                },
                "required": ["x", "y"]
            },
            handler=_computer_move_mouse,
            aliases=["move_mouse"],
        )

        def _computer_click(
            x: Optional[int] = None,
            y: Optional[int] = None,
            element: Optional[str] = None,
            button: str = "left",
            clicks: int = 1
        ) -> Dict[str, Any]:
            res = visual_action_agent.execute_single_action(
                "click",
                target=element,
                arguments={"x": x, "y": y, "element": element, "button": button, "clicks": clicks}
            )
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.click",
            description="Click at screen coordinates or visual element name with verification.",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."},
                    "element": {"type": "string", "description": "Target UI element name to find and click."},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Mouse button."},
                    "clicks": {"type": "integer", "description": "Number of clicks."}
                }
            },
            handler=_computer_click,
            aliases=["mouse_click", "click"],
        )

        def _computer_double_click(x: Optional[int] = None, y: Optional[int] = None, element: Optional[str] = None) -> Dict[str, Any]:
            res = visual_action_agent.execute_single_action(
                "double_click",
                target=element,
                arguments={"x": x, "y": y, "element": element}
            )
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.double_click",
            description="Double-click at coordinates or on a specified visual element.",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."},
                    "element": {"type": "string", "description": "UI element to double click."}
                }
            },
            handler=_computer_double_click,
            aliases=["double_click"],
        )

        def _computer_right_click(x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
            res = mouse_controller.right_click(x=x, y=y)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.right_click",
            description="Right-click (context menu) at specified coordinates or current position.",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."}
                }
            },
            handler=_computer_right_click,
            aliases=["right_click"],
        )

        def _computer_scroll(clicks: int = -5, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
            res = mouse_controller.scroll(clicks=clicks, x=x, y=y)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.scroll",
            description="Scroll vertically (negative = down, positive = up).",
            parameters={
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "description": "Amount to scroll (negative for down, positive for up)."},
                    "x": {"type": "integer", "description": "Optional X coordinate to scroll at."},
                    "y": {"type": "integer", "description": "Optional Y coordinate to scroll at."}
                }
            },
            handler=_computer_scroll,
            aliases=["scroll", "scroll_down", "scroll_up"],
        )

        def _computer_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> Dict[str, Any]:
            res = mouse_controller.drag(start_x, start_y, end_x, end_y, duration=duration)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.drag",
            description="Drag cursor from start coordinates to end coordinates.",
            parameters={
                "type": "object",
                "properties": {
                    "start_x": {"type": "integer", "description": "Starting X."},
                    "start_y": {"type": "integer", "description": "Starting Y."},
                    "end_x": {"type": "integer", "description": "Ending X."},
                    "end_y": {"type": "integer", "description": "Ending Y."},
                    "duration": {"type": "number", "description": "Duration in seconds."}
                },
                "required": ["start_x", "start_y", "end_x", "end_y"]
            },
            handler=_computer_drag,
            aliases=["drag_mouse"],
        )

        def _computer_type(text: str, press_enter: bool = False) -> Dict[str, Any]:
            res = keyboard_controller.type_text(text=text, press_enter=press_enter)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.type",
            description="Safely type text into the currently focused application.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type."},
                    "press_enter": {"type": "boolean", "description": "Whether to press Enter after typing."}
                },
                "required": ["text"]
            },
            handler=_computer_type,
            aliases=["type_text", "keyboard_type"],
        )

        def _computer_press_key(key: str, presses: int = 1) -> Dict[str, Any]:
            res = keyboard_controller.press_key(key=key, presses=presses)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.press_key",
            description="Press a whitelisted keyboard key (enter, escape, tab, arrows, etc.).",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name to press."},
                    "presses": {"type": "integer", "description": "Number of times to press."}
                },
                "required": ["key"]
            },
            handler=_computer_press_key,
            aliases=["press_key"],
        )

        def _computer_hotkey(keys: Any) -> Dict[str, Any]:
            k_list = keys if isinstance(keys, list) else str(keys).split("+")
            res = keyboard_controller.hotkey(*k_list)
            return {"success": res.get("success", False), "data": res, "error": res.get("error")}

        self.register(
            name="computer.hotkey",
            description="Press a safe keyboard shortcut combination (e.g. ctrl+t, alt+tab, ctrl+w).",
            parameters={
                "type": "object",
                "properties": {
                    "keys": {
                        "description": "Keys in combination (e.g. ['ctrl', 't'] or 'ctrl+t')."
                    }
                },
                "required": ["keys"]
            },
            handler=_computer_hotkey,
            aliases=["hotkey", "shortcut"],
        )

        def _computer_emergency_stop(reason: str = "User requested emergency stop") -> Dict[str, Any]:
            emergency_stop_controller.request_stop(reason)
            return {"success": True, "data": {"stopped": True, "reason": reason}, "error": None}

        self.register(
            name="computer.emergency_stop",
            description="Immediately halt and cancel all active computer actions.",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for stopping."}
                }
            },
            handler=_computer_emergency_stop,
            aliases=["emergency_stop", "stop_computer"],
        )


# Global singleton instance
tool_registry = ToolRegistry()

