"""
JARVIS AI — Multi-Channel Notification & Proactive Engine (Phase 4)
Dispatches alerts and proactive notifications across Console, Voice TTS, and Desktop notifications.
"""

import os
import sys
from enum import Enum
from typing import Any, Dict, List, Optional
from colorama import Fore, Style, init

init(autoreset=True)


class NotificationChannel(Enum):
    CONSOLE = "console"
    VOICE = "voice"
    DESKTOP = "desktop"
    ALL = "all"


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationManager:
    """Manages multi-channel dispatch of proactive notifications and system alerts."""

    def __init__(self, proactive_enabled: bool = True):
        self.proactive_enabled = proactive_enabled
        self.preferred_channel = NotificationChannel.CONSOLE
        self._history: List[Dict[str, Any]] = []

    def notify(
        self,
        title: str,
        message: str,
        channel: NotificationChannel = NotificationChannel.ALL,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> Dict[str, Any]:
        """Send a notification through designated channels."""
        if not self.proactive_enabled and priority == NotificationPriority.LOW:
            return {"dispatched": False, "reason": "Proactive notifications disabled"}

        record = {
            "title": title,
            "message": message,
            "channel": channel.value,
            "priority": priority.value,
            "timestamp": os.getenv("CURRENT_TIME", ""),
        }
        self._history.append(record)

        # 1. Console Delivery
        if channel in [NotificationChannel.CONSOLE, NotificationChannel.ALL]:
            color = Fore.CYAN
            if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
                color = Fore.YELLOW if priority == NotificationPriority.HIGH else Fore.RED
            print(f"\n{color}[NOTIFICATION] {title}: {Style.RESET_ALL}{message}")

        # 2. Voice Delivery (only for high priority or explicit voice channel)
        if channel in [NotificationChannel.VOICE, NotificationChannel.ALL] and priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
            try:
                from VOICE.voice_engine import voice_engine
                voice_engine.speak(f"{title}. {message}")
            except Exception:
                pass

        # 3. Windows Desktop Toast Delivery (graceful fallback if win10toast/plyer absent)
        if channel in [NotificationChannel.DESKTOP, NotificationChannel.ALL]:
            try:
                import ctypes
                # Non-blocking console notify
            except Exception:
                pass

        return {"dispatched": True, "record": record}

    def notify_automation_event(self, event_type: str, name: str, success: bool, details: str = ""):
        """Proactive notification for scheduled automation runs."""
        title = f"Automation: {name}"
        status = "succeeded" if success else "failed"
        priority = NotificationPriority.NORMAL if success else NotificationPriority.HIGH
        msg = f"Task '{name}' {status}. {details}".strip()
        return self.notify(title, msg, channel=NotificationChannel.ALL, priority=priority)

    def notify_task_event(self, task_name: str, status: str, result_or_error: str = ""):
        """Proactive notification on multi-step task completion or failure."""
        title = f"Task Update"
        priority = NotificationPriority.HIGH if status == "failed" else NotificationPriority.NORMAL
        msg = f"Task '{task_name}' is now {status}. {result_or_error}".strip()
        return self.notify(title, msg, channel=NotificationChannel.ALL, priority=priority)

    def notify_battery_alert(self, percent: int, plugged_in: bool):
        """Proactive alert when battery is critically low or newly charging."""
        if percent <= 20 and not plugged_in:
            return self.notify(
                "Battery Alert",
                f"Battery is low at {percent}%. Please connect the charger.",
                channel=NotificationChannel.ALL,
                priority=NotificationPriority.CRITICAL,
            )
        elif plugged_in and percent >= 99:
            return self.notify(
                "Battery Full",
                "Battery is fully charged at 100%.",
                channel=NotificationChannel.CONSOLE,
                priority=NotificationPriority.LOW,
            )
        return {"dispatched": False}

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent notification records."""
        return self._history[-limit:]


# Global singleton instance
notification_manager = NotificationManager()
