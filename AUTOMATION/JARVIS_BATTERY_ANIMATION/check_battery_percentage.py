"""
JARVIS AI — Battery Percentage Checker
"""

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

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception:
    speak = print


def battery_percentage():
    """Speak current battery percentage."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            speak("Sir, this device does not have a battery sensor.")
            return

        percent = int(battery.percent)
        speak(f"Sir, our current battery level is {percent} percent.")
    except Exception as e:
        speak(f"Error checking battery: {e}")