"""
JARVIS AI — Monitor Awareness and Screen Topology
Discovers connected monitors, screen resolutions, coordinates bounds, and DPI scaling.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Any

# Windows ctypes helpers
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes


class MonitorInfo:
    def __init__(
        self,
        index: int,
        left: int,
        top: int,
        width: int,
        height: int,
        is_primary: bool = False,
        name: str = "Generic Monitor",
    ):
        self.index = index
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.right = left + width
        self.bottom = top + height
        self.is_primary = is_primary
        self.name = name

    def contains_point(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
            "right": self.right,
            "bottom": self.bottom,
            "is_primary": self.is_primary,
            "name": self.name,
        }


class MonitorManager:
    """Manages monitor topology and screen dimension queries."""

    def __init__(self):
        self._monitors: List[MonitorInfo] = []
        self.refresh_monitors()

    def refresh_monitors(self) -> List[MonitorInfo]:
        """Query and cache current monitor topology."""
        monitors: List[MonitorInfo] = []

        if IS_WINDOWS:
            try:
                monitors = self._query_windows_monitors()
            except Exception:
                monitors = []

        # Fallback to mss if windows ctypes produced nothing
        if not monitors:
            try:
                import mss
                with mss.mss() as sct:
                    for i, m in enumerate(sct.monitors[1:], start=1):
                        monitors.append(
                            MonitorInfo(
                                index=i,
                                left=m["left"],
                                top=m["top"],
                                width=m["width"],
                                height=m["height"],
                                is_primary=(i == 1),
                                name=f"Monitor {i}",
                            )
                        )
            except Exception:
                pass

        # Fallback to system metrics or default 1920x1080
        if not monitors:
            w, h = 1920, 1080
            if IS_WINDOWS:
                try:
                    w = ctypes.windll.user32.GetSystemMetrics(0) or 1920
                    h = ctypes.windll.user32.GetSystemMetrics(1) or 1080
                except Exception:
                    pass
            monitors.append(
                MonitorInfo(
                    index=1,
                    left=0,
                    top=0,
                    width=w,
                    height=h,
                    is_primary=True,
                    name="Primary Display",
                )
            )

        self._monitors = monitors
        return self._monitors

    def _query_windows_monitors(self) -> List[MonitorInfo]:
        user32 = ctypes.windll.user32

        # Enable per-monitor DPI awareness if available
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass

        results: List[MonitorInfo] = []

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFOEX(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", ctypes.c_wchar * 32),
            ]

        MONITOR_DEFAULTTOPRIMARY = 1
        MONITORINFOF_PRIMARY = 1

        monitors_list = []

        def enum_monitor_callback(hmonitor, hdc, lprect, lparam):
            mi = MONITORINFOEX()
            mi.cbSize = ctypes.sizeof(MONITORINFOEX)
            if user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
                monitors_list.append((
                    mi.rcMonitor.left,
                    mi.rcMonitor.top,
                    mi.rcMonitor.right - mi.rcMonitor.left,
                    mi.rcMonitor.bottom - mi.rcMonitor.top,
                    bool(mi.dwFlags & MONITORINFOF_PRIMARY),
                    mi.szDevice,
                ))
            return True

        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(RECT),
            wintypes.LPARAM,
        )

        user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(enum_monitor_callback), 0)

        for idx, (l, t, w, h, is_prim, name) in enumerate(monitors_list, start=1):
            results.append(
                MonitorInfo(
                    index=idx,
                    left=l,
                    top=t,
                    width=w,
                    height=h,
                    is_primary=is_prim,
                    name=name or f"Display {idx}",
                )
            )

        return results

    def get_all_monitors(self) -> List[MonitorInfo]:
        if not self._monitors:
            self.refresh_monitors()
        return self._monitors

    def get_primary_monitor(self) -> MonitorInfo:
        monitors = self.get_all_monitors()
        for m in monitors:
            if m.is_primary:
                return m
        return monitors[0]

    def get_monitor_by_index(self, index: int) -> Optional[MonitorInfo]:
        for m in self.get_all_monitors():
            if m.index == index:
                return m
        return None

    def get_screen_dimensions(self, monitor_index: Optional[int] = None) -> Tuple[int, int]:
        """Returns (width, height) for specified monitor or primary."""
        if monitor_index is not None:
            m = self.get_monitor_by_index(monitor_index)
            if m:
                return m.width, m.height
        pm = self.get_primary_monitor()
        return pm.width, pm.height

    def is_point_within_bounds(self, x: int, y: int) -> bool:
        """Validate if coordinates fall within any active monitor boundary."""
        for m in self.get_all_monitors():
            if m.contains_point(x, y):
                return True
        return False

    def get_virtual_screen_bounds(self) -> Tuple[int, int, int, int]:
        """Returns (left, top, total_width, total_height) covering all monitors."""
        monitors = self.get_all_monitors()
        min_x = min(m.left for m in monitors)
        min_y = min(m.top for m in monitors)
        max_x = max(m.right for m in monitors)
        max_y = max(m.bottom for m in monitors)
        return min_x, min_y, max_x - min_x, max_y - min_y


monitor_manager = MonitorManager()
