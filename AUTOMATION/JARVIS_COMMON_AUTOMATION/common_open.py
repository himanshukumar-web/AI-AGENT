import time
import pyautogui as ui
import random
import importlib.util
import os

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

dlg_path = os.path.join(project_root, 'DATA', 'DLG.py')
speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')

try:
    dlg_module = import_module_from_path('DLG', dlg_path)
    open_dld = dlg_module.open_dld
    
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing modules in common_open: {e}")
    open_dld = ["Opening"]
    speak = print

# M A I N   C O D E

def open(text):
    if open_dld:
        x = random.choice(open_dld)
        speak(x+""+text)
    else:
        speak(f"Opening {text}")
        
    time.sleep(0.5)
    ui.hotkey("win")
    time.sleep(0.2)
    ui.write(text)
    time.sleep(0.5)
    ui.press("enter")
