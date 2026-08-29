"""
JARVIS AI — Main Entry Point
Voice-controlled AI assistant with automation capabilities.

Usage: python main.py
"""

import importlib.util
import os
import sys
import threading
import time
import signal


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Path Resolution ──────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))

# ── Module Paths ─────────────────────────────────────────────────────────────
listen_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_LISTEN', 'listen.py')
speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
brain1_path = os.path.join(project_root, 'BRAIN', 'MAIN_BRAIN', 'brain1.py')
battery_alert_path = os.path.join(project_root, 'AUTOMATION', 'JARVIS_BATTERY_ANIMATION', 'battery_alert.py')
wish_path = os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'WISH_GREATINGS', 'wish.py')
welcome_path = os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'WELCOME_GREATINGS', 'welcome.py')
automation_manager_path = os.path.join(project_root, 'AUTOMATION', 'automation_manager.py')

# ── Load Modules ─────────────────────────────────────────────────────────────
print("=" * 50)
print("  JARVIS AI — Initializing...")
print("=" * 50)

try:
    listen_module = import_module_from_path('listen', listen_path)
    listen = listen_module.listen
    print("  [OK] Speech recognition loaded")
except Exception as e:
    print(f"  [FAIL] Speech recognition: {e}")
    listen = lambda: ""

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
    print("  [OK] Text-to-speech loaded")
except Exception as e:
    print(f"  [FAIL] Text-to-speech: {e}")
    speak = lambda x: print(f"JARVIS (fallback): {x}")

try:
    brain1_module = import_module_from_path('brain1', brain1_path)
    brain_cmd = brain1_module.brain_cmd
    print("  [OK] Brain loaded")
except Exception as e:
    print(f"  [FAIL] Brain: {e}")
    brain_cmd = lambda x: f"I heard '{x}' but my brain is offline."

try:
    battery_module = import_module_from_path('battery_alert', battery_alert_path)
    battery_alert = battery_module.battery_alert
    print("  [OK] Battery monitor loaded")
except Exception as e:
    print(f"  [FAIL] Battery monitor: {e}")
    battery_alert = lambda: None

try:
    wish_module = import_module_from_path('wish', wish_path)
    wish = wish_module.wish
    print("  [OK] Greeting system loaded")
except Exception as e:
    print(f"  [FAIL] Greeting system: {e}")
    wish = lambda: None

try:
    welcome_module = import_module_from_path('welcome', welcome_path)
    welcome = welcome_module.welcome
    print("  [OK] Welcome system loaded")
except Exception as e:
    print(f"  [FAIL] Welcome system: {e}")
    welcome = lambda: None

# Automation scheduler
try:
    auto_manager = import_module_from_path('automation_manager', automation_manager_path)
    start_scheduler = auto_manager.start_scheduler
    print("  [OK] Automation manager loaded")
except Exception as e:
    print(f"  [FAIL] Automation manager: {e}")
    start_scheduler = lambda: None

print("=" * 50)


# ── Background Services ─────────────────────────────────────────────────────
def start_battery_monitor():
    """Run battery monitoring in background."""
    try:
        battery_alert()
    except Exception as e:
        print(f"Battery monitor error: {e}")


# ── Shutdown Handler ─────────────────────────────────────────────────────────
_running = True


def shutdown_handler(signum=None, frame=None):
    """Graceful shutdown."""
    global _running
    _running = False
    print("\n\nJARVIS shutting down...")
    speak("Goodbye sir. Jarvis is going offline.")
    sys.exit(0)


# ── Main Loop ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, shutdown_handler)

    # Start background services
    battery_thread = threading.Thread(target=start_battery_monitor, daemon=True)
    battery_thread.start()

    # Start automation scheduler
    try:
        start_scheduler()
    except Exception as e:
        print(f"Scheduler start error: {e}")

    # Startup sequence
    print("\n  Jarvis is online and listening...")
    speak("Jarvis is online and ready.")
    wish()       # Time-based greeting
    welcome()    # Welcome message

    print("\n  Say 'Jarvis' followed by your command.")
    print("  Press Ctrl+C to exit.\n")

    while _running:
        try:
            text = listen()
            if not text:
                continue

            text = text.lower().strip()

            if text:
                print(f"\n  You said: {text}")

                # Check for wake word
                if "jarvis" in text:
                    response = brain_cmd(text)
                    if response:
                        speak(response)

                    # Check for stop/sleep command
                    if any(kw in text for kw in ["go to sleep", "stop listening", "jarvis sleep"]):
                        print("\n  Jarvis is sleeping. Say 'Jarvis' to wake up.")
                        # Don't exit, just continue listening for wake word

                else:
                    print("  (Wake word 'Jarvis' not detected)")

        except KeyboardInterrupt:
            shutdown_handler()
        except Exception as e:
            print(f"  Error in main loop: {e}")
            time.sleep(1)