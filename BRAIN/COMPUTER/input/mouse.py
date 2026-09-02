"""
JARVIS AI — Controlled Mouse Controller
Executes bounded, validated mouse operations with coordinate safety checks,
failsafe protection, and desktop attachment.
"""

import sys
import time
from typing import Optional, Tuple, Dict, Any
import pyautogui

from BRAIN.COMPUTER.screen.monitor import monitor_manager
from BRAIN.COMPUTER.screen.capture import DesktopAttachment

# Configure PyAutoGUI failsafe
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class MouseController:
    """Controlled, boundary-checked mouse action executor."""

    def __init__(self):
        self._last_position: Tuple[int, int] = (0, 0)

    def get_position(self) -> Tuple[int, int]:
        """Get current mouse cursor (x, y) coordinates."""
        with DesktopAttachment():
            pos = pyautogui.position()
            self._last_position = (pos.x, pos.y)
            return self._last_position

    def validate_coordinates(self, x: int, y: int) -> Tuple[bool, str]:
        """
        Ensure coordinates fall inside an active monitor boundary.
        Prevents clicking off-screen or negative coordinate bugs.
        """
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return False, f"Invalid coordinate types: x={type(x)}, y={type(y)}"

        ix, iy = int(round(x)), int(round(y))
        if not monitor_manager.is_point_within_bounds(ix, iy):
            w, h = monitor_manager.get_screen_dimensions()
            return False, f"Coordinates ({ix}, {iy}) are outside active screen bounds (Primary: {w}x{h})"

        return True, ""

    def move_mouse(self, x: int, y: int, duration: float = 0.2) -> Dict[str, Any]:
        """Move cursor smoothly to target coordinates after boundary validation."""
        valid, err = self.validate_coordinates(x, y)
        if not valid:
            return {"success": False, "error": err}

        ix, iy = int(round(x)), int(round(y))
        try:
            with DesktopAttachment():
                pyautogui.moveTo(ix, iy, duration=max(0.0, min(duration, 2.0)))
                time.sleep(0.05)
                self._last_position = (ix, iy)
            return {"success": True, "action": "move_mouse", "x": ix, "y": iy}
        except Exception as e:
            return {"success": False, "error": f"Mouse move failed: {str(e)}"}

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
    ) -> Dict[str, Any]:
        """
        Execute a single or multi-click at optional (x, y) coordinates.
        If (x, y) omitted, clicks at current cursor position.
        """
        button = button.lower()
        if button not in ("left", "right", "middle"):
            return {"success": False, "error": f"Invalid mouse button: {button}"}

        if x is not None and y is not None:
            valid, err = self.validate_coordinates(x, y)
            if not valid:
                return {"success": False, "error": err}
            target_x, target_y = int(round(x)), int(round(y))
        else:
            target_x, target_y = self.get_position()

        try:
            with DesktopAttachment():
                pyautogui.click(x=target_x, y=target_y, clicks=max(1, min(clicks, 3)), button=button)
                time.sleep(0.08)
                self._last_position = (target_x, target_y)
            return {
                "success": True,
                "action": "click",
                "x": target_x,
                "y": target_y,
                "button": button,
                "clicks": clicks,
            }
        except Exception as e:
            return {"success": False, "error": f"Mouse click failed: {str(e)}"}

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """Execute double-click at target coordinates."""
        return self.click(x=x, y=y, button="left", clicks=2)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """Execute right-click (context menu) at target coordinates."""
        return self.click(x=x, y=y, button="right", clicks=1)

    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """
        Scroll mouse wheel vertically.
        Positive = scroll up, Negative = scroll down.
        """
        if x is not None and y is not None:
            valid, err = self.validate_coordinates(x, y)
            if not valid:
                return {"success": False, "error": err}
            self.move_mouse(x, y, duration=0.1)

        try:
            with DesktopAttachment():
                # Cap clicks to reasonable step count to prevent runaway scrolling
                clamped_clicks = max(-50, min(clicks, 50))
                pyautogui.scroll(clamped_clicks)
                time.sleep(0.05)
            return {"success": True, "action": "scroll", "clicks": clamped_clicks}
        except Exception as e:
            return {"success": False, "error": f"Scroll failed: {str(e)}"}

    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
    ) -> Dict[str, Any]:
        """Drag from starting coordinates to ending coordinates."""
        v1, err1 = self.validate_coordinates(start_x, start_y)
        if not v1:
            return {"success": False, "error": f"Start position: {err1}"}

        v2, err2 = self.validate_coordinates(end_x, end_y)
        if not v2:
            return {"success": False, "error": f"End position: {err2}"}

        sx, sy = int(round(start_x)), int(round(start_y))
        ex, ey = int(round(end_x)), int(round(end_y))

        try:
            with DesktopAttachment():
                pyautogui.moveTo(sx, sy)
                time.sleep(0.05)
                pyautogui.dragTo(ex, ey, duration=max(0.1, min(duration, 3.0)), button="left")
                time.sleep(0.05)
                self._last_position = (ex, ey)
            return {
                "success": True,
                "action": "drag",
                "start": (sx, sy),
                "end": (ex, ey),
            }
        except Exception as e:
            return {"success": False, "error": f"Drag failed: {str(e)}"}


mouse_controller = MouseController()
