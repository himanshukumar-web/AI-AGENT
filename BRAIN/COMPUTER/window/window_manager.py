"""
JARVIS AI — Controlled Window Manager
Provides window introspection, application awareness, window state control,
and safe window focusing using native Windows APIs with desktop attachment.
"""

import sys
import time
from typing import List, Optional, Union, Dict, Any

from BRAIN.COMPUTER.screen.capture import DesktopAttachment

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes


class WindowManager:
    """Manages window discovery, application awareness, and focus control."""

    def __init__(self):
        self._target_application: Optional[str] = None

    def get_target_application(self) -> Optional[str]:
        """Returns the currently targeted application context."""
        return self._target_application

    def set_target_application(self, app_name: Optional[str]):
        """Sets the currently targeted application context."""
        self._target_application = app_name

    def get_active_window(self) -> Dict[str, Any]:
        """
        Get structured information about the currently focused foreground window.
        Returns {hwnd, title, bounds, is_minimized, is_maximized, app_name}.
        """
        if not IS_WINDOWS:
            return {"hwnd": 0, "title": "Mock Desktop Window", "bounds": [0, 0, 1920, 1080], "app_name": "MockApp"}

        user32 = ctypes.windll.user32
        with DesktopAttachment():
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return {"hwnd": 0, "title": "", "bounds": [0, 0, 0, 0], "app_name": ""}

            return self._get_window_info(hwnd)

    def _get_window_info(self, hwnd: int) -> Dict[str, Any]:
        user32 = ctypes.windll.user32

        # Title
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value.strip()

        # Bounds
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        # Status
        # SW_SHOWMINIMIZED = 2, SW_SHOWMAXIMIZED = 3
        # IsIconic checks minimized, IsZoomed checks maximized
        is_minimized = bool(user32.IsIconic(hwnd))
        is_maximized = bool(user32.IsZoomed(hwnd))

        # Approximate app name from title
        app_name = self._extract_app_name(title)

        return {
            "hwnd": hwnd,
            "title": title,
            "bounds": [rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top],
            "is_minimized": is_minimized,
            "is_maximized": is_maximized,
            "app_name": app_name,
        }

    def _extract_app_name(self, title: str) -> str:
        """Extract application name from window title string."""
        if not title:
            return "Unknown"
        parts = title.split(" - ")
        if len(parts) > 1:
            return parts[-1].strip()
        return title[:30]

    def list_windows(self, include_minimized: bool = False) -> List[Dict[str, Any]]:
        """
        List all visible, named desktop windows.
        """
        if not IS_WINDOWS:
            return [{"hwnd": 1, "title": "Chrome", "bounds": [0, 0, 1920, 1080], "app_name": "Chrome"}]

        user32 = ctypes.windll.user32
        results: List[Dict[str, Any]] = []

        def enum_proc(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                is_min = bool(user32.IsIconic(hwnd))
                if not include_minimized and is_min:
                    return True

                buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, buf, 512)
                title = buf.value.strip()

                # Filter out invisible tooltips, shell components without titles
                if title and title not in ("Program Manager", "Windows Shell Experience Host"):
                    info = self._get_window_info(hwnd)
                    results.append(info)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        with DesktopAttachment():
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)

        return results

    def find_window(self, query: str) -> Optional[Dict[str, Any]]:
        """Find a window matching a query string (case-insensitive substring)."""
        q = query.lower().strip()
        windows = self.list_windows(include_minimized=True)

        # 1. Exact match
        for w in windows:
            if q == w["title"].lower() or q == w["app_name"].lower():
                return w

        # 2. Substring match
        for w in windows:
            if q in w["title"].lower() or q in w["app_name"].lower():
                return w

        return None

    def focus_window(self, title_or_hwnd: Union[str, int]) -> Dict[str, Any]:
        """
        Bring the specified window to the foreground and set focus.
        """
        if not IS_WINDOWS:
            return {"success": True, "action": "focus_window", "title": str(title_or_hwnd)}

        user32 = ctypes.windll.user32
        hwnd = None

        if isinstance(title_or_hwnd, int):
            hwnd = title_or_hwnd
        else:
            found = self.find_window(str(title_or_hwnd))
            if found:
                hwnd = found["hwnd"]

        if not hwnd:
            return {"success": False, "error": f"Window '{title_or_hwnd}' could not be located."}

        with DesktopAttachment():
            # If minimized, restore first (SW_RESTORE = 9)
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)
                time.sleep(0.05)

            # Bring to front
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.08)

        info = self._get_window_info(hwnd)
        self._target_application = info["app_name"]
        return {"success": True, "action": "focus_window", "window": info}

    def minimize_window(self, title_or_hwnd: Union[str, int]) -> Dict[str, Any]:
        """Minimize specified window (SW_MINIMIZE = 6)."""
        if not IS_WINDOWS:
            return {"success": True, "action": "minimize_window"}

        user32 = ctypes.windll.user32
        hwnd = title_or_hwnd if isinstance(title_or_hwnd, int) else None
        if not hwnd:
            found = self.find_window(str(title_or_hwnd))
            hwnd = found["hwnd"] if found else None

        if not hwnd:
            return {"success": False, "error": f"Window '{title_or_hwnd}' not found."}

        with DesktopAttachment():
            user32.ShowWindow(hwnd, 6)
        return {"success": True, "action": "minimize_window", "hwnd": hwnd}

    def maximize_window(self, title_or_hwnd: Union[str, int]) -> Dict[str, Any]:
        """Maximize specified window (SW_MAXIMIZE = 3)."""
        if not IS_WINDOWS:
            return {"success": True, "action": "maximize_window"}

        user32 = ctypes.windll.user32
        hwnd = title_or_hwnd if isinstance(title_or_hwnd, int) else None
        if not hwnd:
            found = self.find_window(str(title_or_hwnd))
            hwnd = found["hwnd"] if found else None

        if not hwnd:
            return {"success": False, "error": f"Window '{title_or_hwnd}' not found."}

        with DesktopAttachment():
            user32.ShowWindow(hwnd, 3)
        return {"success": True, "action": "maximize_window", "hwnd": hwnd}

    def restore_window(self, title_or_hwnd: Union[str, int]) -> Dict[str, Any]:
        """Restore specified window from minimized/maximized state (SW_RESTORE = 9)."""
        if not IS_WINDOWS:
            return {"success": True, "action": "restore_window"}

        user32 = ctypes.windll.user32
        hwnd = title_or_hwnd if isinstance(title_or_hwnd, int) else None
        if not hwnd:
            found = self.find_window(str(title_or_hwnd))
            hwnd = found["hwnd"] if found else None

        if not hwnd:
            return {"success": False, "error": f"Window '{title_or_hwnd}' not found."}

        with DesktopAttachment():
            user32.ShowWindow(hwnd, 9)
        return {"success": True, "action": "restore_window", "hwnd": hwnd}

    def close_window(self, title_or_hwnd: Union[str, int]) -> Dict[str, Any]:
        """
        Gracefully request window close via WM_CLOSE (0x0010).
        Never violently kills the process without graceful signal.
        """
        if not IS_WINDOWS:
            return {"success": True, "action": "close_window"}

        user32 = ctypes.windll.user32
        hwnd = title_or_hwnd if isinstance(title_or_hwnd, int) else None
        title = str(title_or_hwnd)
        if not hwnd:
            found = self.find_window(title)
            if found:
                hwnd = found["hwnd"]
                title = found["title"]

        if not hwnd:
            return {"success": False, "error": f"Window '{title_or_hwnd}' not found."}

        WM_CLOSE = 0x0010
        with DesktopAttachment():
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            time.sleep(0.1)

        return {"success": True, "action": "close_window", "title": title, "hwnd": hwnd}


window_manager = WindowManager()
