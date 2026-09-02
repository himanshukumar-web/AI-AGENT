"""
JARVIS AI — Computer Control & Vision Skill Module
Encapsulates screen perception, window management, controlled mouse/keyboard actions,
safety policy checks, and emergency stop capabilities.
"""

from typing import Any, Dict, List, Optional
from SKILLS.base_skill import BaseSkill, SkillCategory

from BRAIN.COMPUTER.screen.capture import screen_capture
from BRAIN.COMPUTER.screen.monitor import monitor_manager
from BRAIN.COMPUTER.input.mouse import mouse_controller
from BRAIN.COMPUTER.input.keyboard import keyboard_controller
from BRAIN.COMPUTER.window.window_manager import window_manager
from BRAIN.COMPUTER.vision.element_detector import ui_element_detector
from BRAIN.COMPUTER.vision.screen_analyzer import screen_analyzer
from BRAIN.COMPUTER.safety.emergency_stop import emergency_stop_controller
from BRAIN.COMPUTER.visual_agent import visual_action_agent


class ComputerSkill(BaseSkill):
    """Provides controlled computer use and screen vision capabilities."""

    def __init__(self):
        super().__init__(
            name="computer",
            description="Perceives the screen, locates UI elements, manages windows, and executes controlled mouse and keyboard actions.",
            category=SkillCategory.SYSTEM,
            version="1.0.0",
        )

    def initialize(self):
        # 1. Screenshot
        self.register_tool(
            name="computer.screenshot",
            description="Capture the desktop screen on-demand without persistent leaks.",
            parameters={
                "type": "object",
                "properties": {
                    "save_temp": {"type": "boolean", "description": "Whether to save to a temporary file."},
                    "monitor_index": {"type": "integer", "description": "Monitor index (default primary)."}
                }
            },
            handler=lambda save_temp=False, monitor_index=None: {
                "success": True,
                "data": {"size": list(screen_capture.capture_screen(monitor_index=monitor_index).size)}
            },
            risk_level="low",
            aliases=["screenshot", "take_screenshot"],
        )

        # 2. Active Window
        self.register_tool(
            name="computer.get_active_window",
            description="Get details about the currently focused foreground window.",
            parameters={"type": "object", "properties": {}},
            handler=lambda: {"success": True, "data": window_manager.get_active_window()},
            risk_level="low",
            aliases=["get_active_window", "active_window"],
        )

        # 3. List Windows
        self.register_tool(
            name="computer.list_windows",
            description="List visible applications and desktop windows.",
            parameters={"type": "object", "properties": {}},
            handler=lambda: {"success": True, "data": window_manager.list_windows()},
            risk_level="low",
            aliases=["list_windows"],
        )

        # 4. Focus Window
        self.register_tool(
            name="computer.focus_window",
            description="Bring an open window or application into active focus.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or app name of the window to focus."}
                },
                "required": ["title"]
            },
            handler=lambda title: window_manager.focus_window(title),
            risk_level="medium",
            aliases=["focus_window"],
        )

        # 5. Screen Analysis
        self.register_tool(
            name="computer.analyze_screen",
            description="Analyze visual desktop contents, active applications, and UI elements.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question or prompt about the screen."}
                }
            },
            handler=lambda query="Describe what is on screen": {"success": True, "data": screen_analyzer.analyze_screen(query)},
            risk_level="low",
            aliases=["analyze_screen", "what_is_on_screen"],
        )

        # 6. Click
        self.register_tool(
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
            handler=lambda x=None, y=None, element=None, button="left", clicks=1: visual_action_agent.execute_single_action(
                "click", target=element, arguments={"x": x, "y": y, "element": element, "button": button, "clicks": clicks}
            ),
            risk_level="medium",
            aliases=["click", "mouse_click"],
        )

        # 7. Type Text
        self.register_tool(
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
            handler=lambda text, press_enter=False: keyboard_controller.type_text(text=text, press_enter=press_enter),
            risk_level="medium",
            aliases=["type_text"],
        )

        # 8. Scroll
        self.register_tool(
            name="computer.scroll",
            description="Scroll vertically (negative = down, positive = up).",
            parameters={
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "description": "Amount to scroll (negative for down, positive for up)."}
                }
            },
            handler=lambda clicks=-5: mouse_controller.scroll(clicks=clicks),
            risk_level="low",
            aliases=["scroll"],
        )

        # 9. Emergency Stop
        self.register_tool(
            name="computer.emergency_stop",
            description="Immediately halt and cancel all active computer actions.",
            parameters={"type": "object", "properties": {}},
            handler=lambda reason="User requested emergency stop": {
                "success": True,
                "data": {"stopped": emergency_stop_controller.request_stop(reason)}
            },
            risk_level="low",
            aliases=["emergency_stop", "stop_computer"],
        )

    def get_capabilities_list(self) -> List[str]:
        """Returns concise list of user-facing computer capabilities."""
        return [
            "Screen Vision: I can see your screen and describe open windows or content.",
            "UI Element Discovery: I can detect buttons, search boxes, links, and tabs.",
            "Window Management: I can check active windows, list open apps, switch focus, or close windows.",
            "Controlled Mouse & Keyboard: I can move the cursor, click targets, scroll, type text, and press safe keys.",
            "Safety & Emergency Stop: All actions respect boundary limits, sensitive UI is protected, and saying 'stop' immediately halts actions.",
        ]
