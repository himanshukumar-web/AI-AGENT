"""
JARVIS AI — Battery Plug Status Checker
"""

import psutil
import importlib.util
import os
import random


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
    plug_in = dlg_module.plug_in
    plug_out = dlg_module.plug_out
except Exception:
    plug_in, plug_out = [], []


def check_plugin_status1():
    """Speak whether charger is plugged in or on battery."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            speak("Sir, this device is connected directly to external power.")
            return

        if battery.power_plugged:
            if plug_in:
                speak(random.choice(plug_in))
            else:
                speak("The charger is currently plugged in and charging.")
        else:
            if plug_out:
                speak(random.choice(plug_out))
            else:
                speak("The charger is disconnected, running on battery power.")
    except Exception as e:
        speak(f"Error checking charger status: {e}")
