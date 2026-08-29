"""
JARVIS AI — Battery Percentage Reporter
Reports current battery level via speech.
"""

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

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak: {e}")
    speak = print


def battery_percentage():
    """Report the current battery percentage."""
    battery = psutil.sensors_battery()
    if battery:
        percent = int(battery.percent)
        speak(f"The device is running on {percent}% battery power.")
    else:
        speak("Unable to read battery information.")