"""
Screen Capture and Monitor Awareness package for JARVIS AI.
"""

from .monitor import MonitorManager, monitor_manager
from .capture import ScreenCapture, screen_capture

__all__ = ["MonitorManager", "monitor_manager", "ScreenCapture", "screen_capture"]
