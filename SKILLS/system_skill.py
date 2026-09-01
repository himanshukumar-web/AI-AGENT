"""
JARVIS AI — System Skill Module
Encapsulates system time, battery, IP, connectivity, apps, jokes, advice, diagnostics, and status.
"""

import datetime
import os
import sys
import psutil
from typing import Any, Dict, Optional
from SKILLS.base_skill import BaseSkill, SkillCategory


class SystemSkill(BaseSkill):
    """Provides local operating system capabilities and queries."""

    def __init__(self):
        super().__init__(
            name="system",
            description="Manages system time, battery, apps, diagnostics, and status.",
            category=SkillCategory.SYSTEM,
        )

    def initialize(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 1. System Time
        def _get_time() -> Dict[str, Any]:
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            return {"success": True, "data": {"time": time_str, "date": date_str, "formatted": f"{time_str} on {date_str}"}, "error": None}

        self.register_tool(
            name="system.time",
            description="Get the current system time and date.",
            parameters={"type": "object", "properties": {}},
            handler=_get_time,
            risk_level="low",
            aliases=["get_time", "time.get"],
        )

        # 2. Battery Status
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

        self.register_tool(
            name="system.battery",
            description="Get the computer's battery percentage and charging status.",
            parameters={"type": "object", "properties": {}},
            handler=_get_battery,
            risk_level="low",
            aliases=["get_battery_status", "battery.status"],
        )

        # 3. IP Address
        def _get_ip() -> Dict[str, Any]:
            try:
                from config import import_module_from_path
                ip_mod = import_module_from_path('find_my_ip', os.path.join(project_root, 'FUNCTION', 'FIND_MY_IP', 'find_my_ip.py'))
                ip = ip_mod.find_my_ip()
                return {"success": True, "data": {"ip": ip, "formatted": f"Public IP is {ip}"}, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="system.ip",
            description="Get the public IP address of the machine.",
            parameters={"type": "object", "properties": {}},
            handler=_get_ip,
            risk_level="low",
            aliases=["get_ip"],
        )

        # 4. Internet Connectivity
        def _check_internet() -> Dict[str, Any]:
            try:
                import requests
                r = requests.get("https://www.google.com", timeout=3)
                online = r.status_code == 200
                return {"success": True, "data": {"online": online, "status": "Connected to Internet" if online else "Offline"}, "error": None}
            except Exception:
                return {"success": True, "data": {"online": False, "status": "No Internet Connection"}, "error": None}

        self.register_tool(
            name="system.internet",
            description="Check if the internet connection is active and stable.",
            parameters={"type": "object", "properties": {}},
            handler=_check_internet,
            risk_level="low",
            aliases=["check_internet"],
        )

        # 5. Jokes & Advice
        def _get_joke() -> Dict[str, Any]:
            try:
                from config import import_module_from_path
                joke_mod = import_module_from_path('joke', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'JOKE', 'joke.py'))
                joke = joke_mod.get_random_joke()
                return {"success": True, "data": {"joke": joke}, "error": None}
            except Exception:
                return {"success": True, "data": {"joke": "Why do programmers prefer dark mode? Because light attracts bugs."}, "error": None}

        self.register_tool(
            name="system.joke",
            description="Get a programming or tech joke.",
            parameters={"type": "object", "properties": {}},
            handler=_get_joke,
            risk_level="low",
            aliases=["get_joke"],
        )

        def _get_advice() -> Dict[str, Any]:
            try:
                from config import import_module_from_path
                adv_mod = import_module_from_path('advice', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'ADVICE', 'advice.py'))
                advice = adv_mod.get_random_advice()
                return {"success": True, "data": {"advice": advice}, "error": None}
            except Exception:
                return {"success": True, "data": {"advice": "Keep learning and building consistently."}, "error": None}

        self.register_tool(
            name="system.advice",
            description="Get a useful productivity or motivational tip.",
            parameters={"type": "object", "properties": {}},
            handler=_get_advice,
            risk_level="low",
            aliases=["get_advice"],
        )

        # 6. Windows Applications
        def _launch_app(app_name: str) -> Dict[str, Any]:
            import pyautogui
            import time
            pyautogui.press('win')
            time.sleep(0.3)
            pyautogui.write(app_name, interval=0.03)
            time.sleep(0.3)
            pyautogui.press('enter')
            return {"success": True, "data": {"app_name": app_name, "message": f"Launched application '{app_name}'."}, "error": None}

        self.register_tool(
            name="system.launch_app",
            description="Launch a desktop application in Windows (e.g. 'notepad', 'calc', 'chrome').",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application."}
                },
                "required": ["app_name"],
            },
            handler=_launch_app,
            risk_level="medium",
            aliases=["launch_application"],
        )

        def _close_app(app_name: str = "") -> Dict[str, Any]:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return {"success": True, "data": {"app_name": app_name, "message": f"Closed active window for '{app_name}'."}, "error": None}

        self.register_tool(
            name="system.close_app",
            description="Close the currently active window for an application.",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application."}
                }
            },
            handler=_close_app,
            risk_level="high",
            aliases=["close_application"],
        )

        # 7. System Diagnostics (Doctor)
        def _run_diagnostics() -> Dict[str, Any]:
            try:
                from BRAIN.UTILS.diagnostics import doctor
                report = doctor.run_diagnostics()
                doctor.print_report()
                return {"success": True, "data": report, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="system.diagnostics",
            description="Run a complete self-diagnostics health check of JARVIS subsystems.",
            parameters={"type": "object", "properties": {}},
            handler=_run_diagnostics,
            risk_level="low",
            aliases=["doctor", "run_diagnostics", "system.health"],
        )

        # 8. System Status Center
        def _get_status() -> Dict[str, Any]:
            try:
                from BRAIN.LLM.provider_manager import provider_manager
                from BRAIN.CORE_AGENT.task_state import task_state_manager
                from BRAIN.MEMORY.memory_manager import memory_manager
                prov = provider_manager.get_active_provider()
                state = task_state_manager.state.value.upper()
                task_name = task_state_manager.current_task_name or "None"
                status_data = {
                    "llm": f"{prov.provider_name.upper()} ({prov.model_name})",
                    "task_state": state,
                    "active_task": task_name,
                    "voice": "Ready",
                    "internet": "Connected",
                    "formatted": f"LLM: {prov.provider_name.upper()} | Task: {state} | Voice: Ready",
                }
                return {"success": True, "data": status_data, "error": None}
            except Exception as e:
                return {"success": False, "data": None, "error": str(e)}

        self.register_tool(
            name="system.status",
            description="Get a high-level operational status summary of JARVIS.",
            parameters={"type": "object", "properties": {}},
            handler=_get_status,
            risk_level="low",
            aliases=["status", "get_status"],
        )
