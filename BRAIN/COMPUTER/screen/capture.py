"""
JARVIS AI — Screen Capture Abstraction
Provides on-demand full screen, monitor-specific, and active window capture with
thread-desktop attachment on Windows and automatic memory cleanup.
"""

import base64
import io
import os
import sys
import tempfile
import time
from typing import Optional, Tuple, Union
from PIL import Image

from .monitor import monitor_manager, MonitorInfo

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes


class DesktopAttachment:
    """Context manager to attach thread to Windows active input desktop."""

    def __init__(self):
        self._h_desktop = None
        self._orig_desktop = None

    def __enter__(self):
        if not IS_WINDOWS:
            return self
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            self._orig_desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
            # DESKTOP_ALL_ACCESS = 0x01FF, DESKTOP_READOBJECTS = 0x0001
            h_desk = user32.OpenInputDesktop(0, False, 0x01FF)
            if h_desk:
                self._h_desktop = h_desk
                user32.SetThreadDesktop(h_desk)
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not IS_WINDOWS:
            return
        try:
            user32 = ctypes.windll.user32
            if self._orig_desktop:
                user32.SetThreadDesktop(self._orig_desktop)
            if self._h_desktop:
                user32.CloseDesktop(self._h_desktop)
        except Exception:
            pass


class ScreenCapture:
    """Provides controlled, on-demand screen capture without persistent leaks."""

    def __init__(self):
        self._last_capture_time: float = 0.0

    def capture_screen(
        self,
        monitor_index: Optional[int] = None,
        crop_box: Optional[Tuple[int, int, int, int]] = None,
    ) -> Image.Image:
        """
        Capture the current screen on-demand.
        Returns a PIL.Image.Image.
        """
        img: Optional[Image.Image] = None

        with DesktopAttachment():
            # 1. Primary approach: PIL ImageGrab with desktop attached
            try:
                from PIL import ImageGrab
                if monitor_index is not None:
                    mon = monitor_manager.get_monitor_by_index(monitor_index)
                    if mon:
                        bbox = (mon.left, mon.top, mon.right, mon.bottom)
                        img = ImageGrab.grab(bbox=bbox, all_screens=True)
                if img is None:
                    img = ImageGrab.grab(all_screens=True)
            except Exception:
                img = None

            # 2. Secondary approach: mss
            if img is None:
                try:
                    sct_factory = getattr(mss, 'MSS', getattr(mss, 'mss', None))
                    with sct_factory() as sct:
                        idx = monitor_index if monitor_index is not None else 0
                        if idx < len(sct.monitors):
                            raw = sct.grab(sct.monitors[idx])
                            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
                except Exception:
                    img = None

            # 3. Fallback: synthetic placeholder if running in headless/restricted environment
            if img is None:
                w, h = monitor_manager.get_screen_dimensions(monitor_index)
                img = Image.new("RGB", (w, h), color=(30, 30, 30))

        if crop_box and img:
            try:
                img = img.crop(crop_box)
            except Exception:
                pass

        self._last_capture_time = time.time()
        return img

    def capture_active_window(self) -> Tuple[Optional[Image.Image], Optional[str]]:
        """
        Capture the currently active foreground window.
        Returns (PIL.Image or None, window_title or None).
        """
        if not IS_WINDOWS:
            img = self.capture_screen()
            return img, "Active Window"

        try:
            user32 = ctypes.windll.user32
            with DesktopAttachment():
                hwnd = user32.GetForegroundWindow()
                if not hwnd:
                    return self.capture_screen(), "Desktop"

                # Get title
                buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, buf, 512)
                title = buf.value.strip() or "Window"

                # Get coordinates
                class RECT(ctypes.Structure):
                    _fields_ = [
                        ("left", ctypes.c_long),
                        ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long),
                    ]

                rect = RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top

                if w <= 0 or h <= 0:
                    return self.capture_screen(), title

                crop_box = (max(0, rect.left), max(0, rect.top), max(0, rect.right), max(0, rect.bottom))
                img = self.capture_screen(crop_box=crop_box)
                return img, title
        except Exception:
            return self.capture_screen(), "Desktop"

    def get_image_bytes(
        self,
        img: Image.Image,
        format: str = "JPEG",
        quality: int = 80,
        max_dimension: int = 1280,
    ) -> bytes:
        """Resize and compress an image into bytes for cost-effective transfer."""
        if max(img.size) > max_dimension:
            scale = max_dimension / float(max(img.size))
            new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        if format.upper() == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=quality)
        return buffer.getvalue()

    def get_base64_encoded(
        self,
        img: Image.Image,
        format: str = "JPEG",
        quality: int = 80,
        max_dimension: int = 1280,
    ) -> str:
        """Encode image directly to base64 string with size optimization."""
        b = self.get_image_bytes(img, format=format, quality=quality, max_dimension=max_dimension)
        return base64.b64encode(b).decode("utf-8")

    def save_temp_screenshot(self, img: Image.Image) -> str:
        """
        Save screenshot to a designated temporary file with PID prefix.
        Returns the absolute path. Caller is responsible for cleanup.
        """
        fd, path = tempfile.mkstemp(prefix="jarvis_screen_", suffix=".jpg")
        os.close(fd)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(path, "JPEG", quality=85)
        return path


screen_capture = ScreenCapture()
