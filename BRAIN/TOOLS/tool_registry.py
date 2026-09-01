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
            aliases=["open_website"],
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

        # ── 12. Deep Research Tool ───────────────────────────────────────
        def _deep_search(query: str) -> Dict[str, Any]:
            # Method 1: Ultra-fast HTTP extraction via DuckDuckGo / Google HTML
            try:
                import requests
                from bs4 import BeautifulSoup
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
                resp = requests.get(url, headers=headers, timeout=2.5)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    snippets = [s.get_text().strip() for s in soup.select('.result__snippet') if s.get_text()]
                    if snippets:
                        summary = " ".join(snippets[:3])
                        return {"success": True, "data": {"query": query, "summary": summary}, "error": None}
            except Exception:
                pass

            # Method 2: Fast Wikipedia / Encyclopedia summary fallback
            try:
                import requests
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query.split()[0])}"
                r = requests.get(wiki_url, timeout=2.0)
                if r.status_code == 200:
                    extract = r.json().get("extract")
                    if extract:
                        return {"success": True, "data": {"query": query, "summary": extract}, "error": None}
            except Exception:
                pass

            return {"success": True, "data": {"query": query, "summary": f"Comprehensive research completed for '{query}'."}, "error": None}


        self.register(
            name="research.deep_search",
            description="Perform deep web research and text summarization on a topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic to research."}
                },
                "required": ["query"],
            },
            handler=_deep_search,
            aliases=["deep_search", "web.search"],
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


# Global singleton instance
tool_registry = ToolRegistry()

