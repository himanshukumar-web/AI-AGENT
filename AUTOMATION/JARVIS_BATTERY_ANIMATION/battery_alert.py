import random
import time
import psutil
import importlib.util
import os

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Dynamic path resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
dlg_path = os.path.join(project_root, 'DATA', 'DLG.py')

# Load modules
try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak: {e}")
    speak = print # Fallback

try:
    dlg_module = import_module_from_path('DLG', dlg_path)
    low_b = dlg_module.low_b
    last_low = dlg_module.last_low
    full_battery = dlg_module.full_battery
except Exception as e:
    print(f"Error importing DLG: {e}")
    low_b = []
    last_low = []
    full_battery = []

# M A I N  C O D E

def battery_alert():
    while True:
        time.sleep(10)
        battery = psutil.sensors_battery()
        if not battery:
            continue
            
        percent = int(battery.percent)

        if percent < 10:
            if last_low:
                random_low = random.choice(last_low)
                speak(random_low)
        elif percent < 30:
            if low_b:
                random_low = random.choice(low_b)
                speak(random_low)
        elif percent == 100:
            if full_battery:
                random_low = random.choice(full_battery)
                speak(random_low)
        else:
            pass

        time.sleep(1500)

def battery_alert1():
        battery = psutil.sensors_battery()
        if not battery:
            return

        percent = int(battery.percent)

        if percent < 10:
            if last_low:
                random_low = random.choice(last_low)
                speak(random_low)
        elif percent < 30:
            if low_b:
                random_low = random.choice(low_b)
                speak(random_low)
        elif percent == 100:
            if full_battery:
                random_low = random.choice(full_battery)
                speak(random_low)
        else:
            speak("sir,your battery is in perfect battery level")
