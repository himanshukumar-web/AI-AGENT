"""
JARVIS AI — Battery Alert Module
Monitors battery percentage and charging state with periodic voice alerts.
Includes defensive checks for desktop PCs without battery sensors.
"""

import random
import time
import psutil
import importlib.util
import os


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
dlg_path = os.path.join(project_root, 'DATA', 'DLG.py')

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception:
    speak = print

try:
    dlg_module = import_module_from_path('DLG', dlg_path)
    low_b = dlg_module.low_b
    last_low = dlg_module.last_low
    full_battery = dlg_module.full_battery
except Exception:
    low_b, last_low, full_battery = [], [], []


def battery_alert():
    """Continuous background battery monitor."""
    while True:
        try:
            battery = psutil.sensors_battery()
            if not battery:
                # Desktop PC or no battery sensor available
                time.sleep(300)
                continue

            percent = int(battery.percent)

            if percent < 10:
                if last_low:
                    speak(random.choice(last_low))
                else:
                    speak(f"Critical battery warning: {percent}% remaining. Please connect your charger immediately.")
            elif percent < 25 and not battery.power_plugged:
                if low_b:
                    speak(random.choice(low_b))
                else:
                    speak(f"Low battery warning: {percent}%. Please plug in the charger.")
            elif percent == 100 and battery.power_plugged:
                if full_battery:
                    speak(random.choice(full_battery))
                else:
                    speak("Battery is fully charged. You can disconnect the charger.")

            time.sleep(300)  # Check every 5 minutes
        except Exception:
            time.sleep(300)


def battery_alert1():
    """One-time battery check and voice alert."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            speak("This system does not have a battery sensor or is connected directly to AC power.")
            return

        percent = int(battery.percent)
        plugged = "plugged in" if battery.power_plugged else "discharging on battery"

        if percent < 10:
            if last_low:
                speak(random.choice(last_low))
            else:
                speak(f"Battery is critically low at {percent}%. Please connect the charger.")
        elif percent < 30:
            if low_b:
                speak(random.choice(low_b))
            else:
                speak(f"Battery is low at {percent}%.")
        elif percent == 100:
            if full_battery:
                speak(random.choice(full_battery))
            else:
                speak("Battery is 100% fully charged.")
        else:
            speak(f"Sir, your battery is at {percent}%, currently {plugged}.")
    except Exception as e:
        speak(f"Could not retrieve battery status: {e}")
