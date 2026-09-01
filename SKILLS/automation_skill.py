"""
JARVIS AI — Automation Skill Module
Encapsulates scheduled, on-demand, and custom automation workflows.
"""

from typing import Any, Dict, Optional
from config import PATHS, import_module_from_path
from SKILLS.base_skill import BaseSkill, SkillCategory


class AutomationSkill(BaseSkill):
    """Provides automation creation, scheduling, execution, and lifecycle management."""

    def __init__(self):
        super().__init__(
            name="automation",
            description="Manages automated tasks, daily reminders, and background routines.",
            category=SkillCategory.AUTOMATION,
        )

    def initialize(self):
        def _create_automation(name: str, action: str, parameters: Optional[Dict[str, Any]] = None, schedule_time: Optional[str] = None) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            auto = mgr.create_automation(name=name, action=action, parameters=parameters or {}, schedule_time=schedule_time)
            if auto:
                return {"success": True, "data": auto, "error": None}
            return {"success": False, "data": None, "error": f"Failed to create automation '{name}'."}

        self.register_tool(
            name="automation.create",
            description="Create a recurring or on-demand automated task in JARVIS.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the automation."},
                    "action": {"type": "string", "description": "Action type (e.g. 'check_time', 'check_battery', 'play_youtube')."},
                    "parameters": {"type": "object", "description": "Action parameters."},
                    "schedule_time": {"type": "string", "description": "Scheduled time in HH:MM format (e.g. '09:00')."}
                },
                "required": ["name", "action"],
            },
            handler=_create_automation,
            risk_level="medium",
            aliases=["create_automation"],
        )

        def _list_automations() -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            autos = mgr.list_automations(speak_output=False)
            return {"success": True, "data": {"count": len(autos), "automations": autos}, "error": None}

        self.register_tool(
            name="automation.list",
            description="List all configured custom automations.",
            parameters={"type": "object", "properties": {}},
            handler=_list_automations,
            risk_level="low",
            aliases=["list_automations", "get_automations"],
        )

        def _update_automation(automation_id: str, **updates) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            res = mgr.edit_automation(automation_id, **updates)
            if res:
                return {"success": True, "data": res, "error": None}
            return {"success": False, "data": None, "error": f"Could not update automation '{automation_id}'."}

        self.register_tool(
            name="automation.update",
            description="Update an existing automation's properties, schedule, or enabled status.",
            parameters={
                "type": "object",
                "properties": {
                    "automation_id": {"type": "string", "description": "The ID of the automation."},
                    "enabled": {"type": "boolean", "description": "Enable or disable status."}
                },
                "required": ["automation_id"],
            },
            handler=_update_automation,
            risk_level="medium",
            aliases=["update_automation"],
        )

        def _delete_automation(automation_id: str) -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            success = mgr.delete_automation(automation_id)
            return {"success": success, "data": {"automation_id": automation_id}, "error": None if success else "Automation not found"}

        self.register_tool(
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
            risk_level="high",
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

        self.register_tool(
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
            risk_level="medium",
            aliases=["run_automation"],
        )

        def _get_history() -> Dict[str, Any]:
            mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])
            logs = mgr.get_automation_history(speak_output=False)
            return {"success": True, "data": {"count": len(logs), "logs": logs[-10:]}, "error": None}

        self.register_tool(
            name="automation.history",
            description="Get recent execution logs of automations.",
            parameters={"type": "object", "properties": {}},
            handler=_get_history,
            risk_level="low",
            aliases=["get_automation_history"],
        )
