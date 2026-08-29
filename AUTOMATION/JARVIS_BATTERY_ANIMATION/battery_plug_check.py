"""
JARVIS AI — Battery Plug/Unplug Detection
Monitors charger connection status and announces changes.
"""

import random
import psutil
import importlib.util
import os


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Dynamic path resolution (replaces hardcoded paths)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
dlg_path = os.path.join(project_root, 'DATA', 'DLG.py')

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak: {e}")
    speak = print

try:
    dlg_module = import_module_from_path('DLG', dlg_path)
    plug_out = dlg_module.plug_out
    plug_in = dlg_module.plug_in
    full_battery = dlg_module.full_battery
except Exception as e:
    print(f"Error importing DLG: {e}")
    plug_out = ["Charger unplugged."]
    plug_in = ["Charger plugged in."]
    full_battery = ["Battery fully charged."]


# M A I N  C O D E

def check_plugin_status():
    """Continuously monitor charger plug/unplug status."""
    battery = psutil.sensors_battery()
    if not battery:
        return
    previous_state = battery.power_plugged

    while True:
        battery = psutil.sensors_battery()
        if not battery:
            continue

        if battery.power_plugged != previous_state:
            if battery.power_plugged:
                random_msg = random.choice(plug_in)
                speak(random_msg)
            else:
                random_msg = random.choice(plug_out)
                speak(random_msg)

            previous_state = battery.power_plugged


previous_state = None
plug_in1 = ["Charger is plugged, check confirmed.", "Battery is charging, charger is plugged. Check completed."]
plug_out1 = ["Charger status: unplugged.", "Battery is not charging, charger is not plugged. Check completed."]


def check_plugin_status1():
    """One-time check of charger plug status."""
    global previous_state

    battery = psutil.sensors_battery()
    if not battery:
        speak("Unable to read battery status.")
        return

    if battery.power_plugged != previous_state:
        if battery.power_plugged:
            random_msg = random.choice(plug_in1)
            speak(random_msg)
        else:
            random_msg = random.choice(plug_out1)
            speak(random_msg)

        previous_state = battery.power_plugged
