"""
JARVIS AI — Main Automation Integration
Central dispatcher that routes voice commands to the appropriate automation subsystem.
This was the missing link — the file was previously empty.
"""

import os
import importlib.util


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current_dir = os.path.dirname(os.path.abspath(__file__))
automation_root = os.path.abspath(os.path.join(current_dir, '..'))

# ── Load Automation Subsystems ───────────────────────────────────────────────
# YouTube integration
try:
    yt_module = import_module_from_path(
        'youtube_intergration',
        os.path.join(automation_root, 'JARVIS_YOUTUBE_AUTOMATION', 'youtube_intergration.py'))
    youtube_cmd = yt_module.youtube_cmd
except Exception as e:
    print(f"Error loading YouTube automation: {e}")
    youtube_cmd = lambda x: None

# Google/Browser integration
try:
    google_module = import_module_from_path(
        'google_integration',
        os.path.join(automation_root, 'JARVIS_GOOGLE_AUTOMATION', 'google_integration.py'))
    google_cmd = google_module.google_cmd
except Exception as e:
    print(f"Error loading Google automation: {e}")
    google_cmd = lambda x: None

# Common (open/close apps) integration
try:
    common_module = import_module_from_path(
        'common_integration',
        os.path.join(automation_root, 'JARVIS_COMMON_AUTOMATION', 'common_integration.py'))
    common_cmd = common_module.common_cmd
except Exception as e:
    print(f"Error loading common automation: {e}")
    common_cmd = lambda x: False

# Battery integration
try:
    battery_module = import_module_from_path(
        'battery_integration',
        os.path.join(automation_root, 'JARVIS_BATTERY_ANIMATION', 'battery_integration.py'))
    battery_cmd = battery_module.battery_cmd
except Exception as e:
    print(f"Error loading battery automation: {e}")
    battery_cmd = lambda x: False

# Automation manager (CRUD + scheduling)
try:
    manager_module = import_module_from_path(
        'automation_manager',
        os.path.join(automation_root, 'automation_manager.py'))
    handle_automation_command = manager_module.handle_automation_command
    start_scheduler = manager_module.start_scheduler
except Exception as e:
    print(f"Error loading automation manager: {e}")
    handle_automation_command = lambda x: False
    start_scheduler = lambda: None


# ── Keywords for routing ─────────────────────────────────────────────────────
YOUTUBE_KEYWORDS = [
    "youtube", "play music", "play song", "gana bajao", "music bajao",
    "play video", "stop music", "play again", "increase volume",
    "decrease volume", "seek forward", "seek backward", "toggle subtitles",
    "toggle play", "toggle mute", "toggle full screen", "toggle theater",
    "toggle miniplayer", "toggle party", "pan up", "pan down",
    "pan left", "pan right", "next video", "previous video",
    "playback speed", "search in youtube", "search on youtube",
    "search in current youtube", "search on current youtube",
    "music play karo", "sing song", "jarvis sing",
]

GOOGLE_KEYWORDS = [
    "search in google", "search on google", "scroll up", "scroll down",
    "scroll to top", "scroll to bottom", "close tab", "open browser menu",
    "zoom in", "zoom out", "refresh page", "switch to next tab",
    "switch to previous tab", "open history", "open bookmarks",
    "go back", "go forward", "open dev tools", "toggle full screen",
    "open private window", "open new tab", "open website", "open site",
]

BATTERY_KEYWORDS = [
    "battery percentage", "battery level", "how much battery",
    "check plug", "charger status", "is charger", "battery alert",
    "battery status",
]

AUTOMATION_KEYWORDS = [
    "automation", "list automation", "show automation", "my automation",
    "run automation", "execute automation", "delete automation",
    "remove automation", "enable automation", "disable automation",
    "create automation", "new automation", "automation history",
    "automation log",
]


def process_automation(text):
    """
    Central automation dispatcher.
    Routes the command to the correct subsystem.
    
    Returns True if the command was handled, False otherwise.
    """
    text_lower = text.lower().strip()

    # 1. Check automation management commands first
    if any(kw in text_lower for kw in AUTOMATION_KEYWORDS):
        result = handle_automation_command(text_lower)
        if result:
            return True

    # 2. Check battery commands
    if any(kw in text_lower for kw in BATTERY_KEYWORDS):
        result = battery_cmd(text_lower)
        if result:
            return True

    # 3. Check YouTube commands
    if any(kw in text_lower for kw in YOUTUBE_KEYWORDS):
        youtube_cmd(text_lower)
        return True

    # 4. Check Google/Browser commands
    if any(kw in text_lower for kw in GOOGLE_KEYWORDS):
        google_cmd(text_lower)
        return True

    # 5. Check open/close commands (catch-all for "open X" / "close")
    if "open" in text_lower or "close" in text_lower or "kholo" in text_lower or "band karo" in text_lower:
        result = common_cmd(text_lower)
        if result:
            return True

    return False
