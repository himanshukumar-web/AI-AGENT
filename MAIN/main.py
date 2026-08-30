"""
JARVIS AI — Main Assistant Entry Point
Voice and text-controlled personal AI assistant with modular automations.

Usage:
    python main.py
    python main.py --cli    (Run in CLI text mode without microphone)
"""

import os
import sys
import threading
import time
import signal
import importlib.util
from colorama import Fore, Style, init

init(autoreset=True)

# ── Ensure Project Root in sys.path ──────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import PATHS, import_module_from_path, USER_NAME, ASSISTANT_NAME

# ── Load Core Modules ────────────────────────────────────────────────────────
print(Fore.CYAN + "=" * 55)
print(Fore.CYAN + f"  {ASSISTANT_NAME.upper()} AI — Initializing Subsystems (Python 3.14.7)")
print(Fore.CYAN + "=" * 55)

try:
    listen_module = import_module_from_path('listen', PATHS['listen'])
    listen = listen_module.listen
    print(Fore.GREEN + "  [OK] Speech Recognition System Loaded")
except Exception as e:
    print(Fore.RED + f"  [FAIL] Speech Recognition: {e}")
    listen = lambda: ""

try:
    speak_module = import_module_from_path('speak', PATHS['speak'])
    speak = speak_module.speak
    print(Fore.GREEN + "  [OK] Text-to-Speech Engine Loaded")
except Exception as e:
    print(Fore.RED + f"  [FAIL] Text-to-Speech: {e}")
    speak = lambda x: print(f"JARVIS: {x}")

try:
    brain1_module = import_module_from_path('brain1', PATHS['brain1'])
    brain_cmd = brain1_module.brain_cmd
    print(Fore.GREEN + "  [OK] Intelligence & Intent Brain Loaded")
except Exception as e:
    print(Fore.RED + f"  [FAIL] Intelligence Brain: {e}")
    brain_cmd = lambda x: f"I heard '{x}' but my neural core is offline."

try:
    battery_alert_path = os.path.join(project_root, 'AUTOMATION', 'JARVIS_BATTERY_ANIMATION', 'battery_alert.py')
    battery_module = import_module_from_path('battery_alert', battery_alert_path)
    battery_alert = battery_module.battery_alert
    print(Fore.GREEN + "  [OK] Battery & Power Monitor Loaded")
except Exception as e:
    print(Fore.YELLOW + f"  [WARN] Battery Monitor: {e}")
    battery_alert = lambda: None

try:
    wish_path = os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'WISH_GREATINGS', 'wish.py')
    wish_module = import_module_from_path('wish', wish_path)
    wish = wish_module.wish
    print(Fore.GREEN + "  [OK] Temporal Greeting System Loaded")
except Exception as e:
    print(Fore.YELLOW + f"  [WARN] Greeting System: {e}")
    wish = lambda: None

try:
    welcome_path = os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'WELCOME_GREATINGS', 'welcome.py')
    welcome_module = import_module_from_path('welcome', welcome_path)
    welcome = welcome_module.welcome
    print(Fore.GREEN + "  [OK] Welcome Subsystem Loaded")
except Exception as e:
    print(Fore.YELLOW + f"  [WARN] Welcome Subsystem: {e}")
    welcome = lambda: None

try:
    auto_manager = import_module_from_path('automation_manager', PATHS['automation_manager'])
    start_scheduler = auto_manager.start_scheduler
    print(Fore.GREEN + "  [OK] Automation Engine & Scheduler Loaded")
except Exception as e:
    print(Fore.YELLOW + f"  [WARN] Automation Manager: {e}")
    start_scheduler = lambda: None

print(Fore.CYAN + "=" * 55)


# ── Background Services ─────────────────────────────────────────────────────
def start_battery_monitor():
    """Run battery monitoring daemon."""
    try:
        battery_alert()
    except Exception:
        pass


# ── Shutdown Handler ─────────────────────────────────────────────────────────
_running = True


def shutdown_handler(signum=None, frame=None):
    """Graceful shutdown handler."""
    global _running
    _running = False
    print(Fore.YELLOW + f"\n\n{ASSISTANT_NAME} shutting down...")
    speak(f"Goodbye {USER_NAME}. {ASSISTANT_NAME} is going offline.")
    sys.exit(0)


# ── Main Entry Point ─────────────────────────────────────────────────────────
def main():
    global _running

    signal.signal(signal.SIGINT, shutdown_handler)

    # Start battery monitoring daemon
    battery_thread = threading.Thread(target=start_battery_monitor, daemon=True)
    battery_thread.start()

    # Start scheduled automation worker
    try:
        start_scheduler()
    except Exception:
        pass

    cli_mode = "--cli" in sys.argv or "-c" in sys.argv

    # Startup Sequence
    print(Fore.CYAN + f"\n  {ASSISTANT_NAME} is online and ready.")
    speak(f"{ASSISTANT_NAME} is online and ready.")
    wish()
    welcome()

    if cli_mode:
        print(Fore.MAGENTA + f"\n  [CLI Mode Active] Type your commands (or 'exit' to quit).\n")
    else:
        print(Fore.MAGENTA + f"\n  Say 'Jarvis' followed by your command, or pass --cli to type.\n  Press Ctrl+C to exit.\n")

    while _running:
        try:
            if cli_mode:
                text = input(Fore.LIGHTGREEN_EX + f"You ({USER_NAME}) > ").strip()
            else:
                text = listen()

            if not text:
                continue

            text_clean = text.strip()

            if cli_mode:
                if text_clean.lower() in ["exit", "quit", "goodbye"]:
                    shutdown_handler()
                response = brain_cmd(text_clean)
                if response:
                    speak(response)
            else:
                # Voice mode: respond if wake word is mentioned or direct command
                if "jarvis" in text_clean.lower() or len(text_clean.split()) > 0:
                    response = brain_cmd(text_clean)
                    if response:
                        speak(response)

                    if any(kw in text_clean.lower() for kw in ["go to sleep", "stop listening"]):
                        print(Fore.YELLOW + f"\n  {ASSISTANT_NAME} is sleeping. Speak again to wake up.")

        except KeyboardInterrupt:
            shutdown_handler()
        except Exception as e:
            print(Fore.RED + f"  Loop error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()