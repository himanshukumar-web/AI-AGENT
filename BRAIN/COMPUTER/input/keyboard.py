"""
JARVIS AI — Controlled Keyboard Controller
Executes whitelisted, validated keystrokes, shortcuts, and typing operations.
"""

import sys
import time
from typing import List, Optional, Set, Dict, Any
import pyautogui

from BRAIN.COMPUTER.screen.capture import DesktopAttachment

# Whitelist of allowed single keys
ALLOWED_KEYS: Set[str] = {
    # Alphanumeric & basic punctuation
    "enter", "return", "esc", "escape", "tab", "space", "backspace", "delete",
    "insert", "home", "end", "pageup", "pagedown",
    # Arrows
    "up", "down", "left", "right",
    # Modifiers
    "ctrl", "alt", "shift", "win",
    # Function keys
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
}

# Whitelist of recognized safe keyboard shortcuts
ALLOWED_SHORTCUTS: Set[str] = {
    # Browser / Navigation
    "ctrl+t", "ctrl+w", "ctrl+r", "ctrl+l", "ctrl+tab", "ctrl+shift+tab", "ctrl+shift+t",
    "ctrl+h", "ctrl+j", "ctrl+d", "ctrl+f", "alt+left", "alt+right", "alt+home",
    # Clipboard / Editing
    "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+y", "ctrl+a", "ctrl+s",
    # Windows navigation
    "alt+tab", "alt+f4", "win+d", "win+e", "win+r", "win+m", "win+up", "win+down",
    "ctrl+shift+esc", "alt+enter",
}


class KeyboardController:
    """Controlled, whitelisted keyboard action executor."""

    def __init__(self):
        pass

    def type_text(
        self,
        text: str,
        interval: float = 0.02,
        press_enter: bool = False,
    ) -> Dict[str, Any]:
        """
        Type text safely with natural key interval.
        Optional press_enter after typing.
        """
        if not text:
            return {"success": False, "error": "Text to type cannot be empty"}

        clamped_interval = max(0.005, min(interval, 0.2))

        try:
            with DesktopAttachment():
                pyautogui.write(text, interval=clamped_interval)
                if press_enter:
                    time.sleep(0.05)
                    pyautogui.press("enter")
                time.sleep(0.05)

            # Redact length in confirmation if large
            preview = text if len(text) <= 30 else f"{text[:27]}..."
            return {"success": True, "action": "type_text", "typed_preview": preview, "length": len(text)}
        except Exception as e:
            return {"success": False, "error": f"Type text failed: {str(e)}"}

    def press_key(self, key: str, presses: int = 1) -> Dict[str, Any]:
        """Press a single whitelisted key."""
        k = key.strip().lower()
        if k not in ALLOWED_KEYS and len(k) > 1:
            return {"success": False, "error": f"Key '{key}' is not in the allowed keys whitelist."}

        num_presses = max(1, min(presses, 10))

        try:
            with DesktopAttachment():
                for _ in range(num_presses):
                    pyautogui.press(k)
                    time.sleep(0.04)
            return {"success": True, "action": "press_key", "key": k, "presses": num_presses}
        except Exception as e:
            return {"success": False, "error": f"Press key failed: {str(e)}"}

    def hotkey(self, *keys: str) -> Dict[str, Any]:
        """
        Execute a multi-key shortcut.
        Validates against safety whitelist or allows single modifier combinations.
        """
        cleaned_keys = [k.strip().lower() for k in keys if k.strip()]
        if not cleaned_keys:
            return {"success": False, "error": "No keys specified for hotkey."}

        combo_str = "+".join(cleaned_keys)

        # Validate combo safety
        is_safe = (
            combo_str in ALLOWED_SHORTCUTS or
            all(k in ALLOWED_KEYS or len(k) == 1 for k in cleaned_keys)
        )

        if not is_safe:
            return {
                "success": False,
                "error": f"Hotkey combination '{combo_str}' is restricted for safety.",
            }

        try:
            with DesktopAttachment():
                pyautogui.hotkey(*cleaned_keys)
                time.sleep(0.08)
            return {"success": True, "action": "hotkey", "combination": combo_str}
        except Exception as e:
            return {"success": False, "error": f"Hotkey execution failed: {str(e)}"}


keyboard_controller = KeyboardController()
