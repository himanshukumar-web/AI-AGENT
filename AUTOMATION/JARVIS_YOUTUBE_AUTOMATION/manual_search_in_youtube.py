"""
JARVIS AI — Manual YouTube Search
Searches within an already-open YouTube window using keyboard automation.
"""

import pyautogui as ui
import time
import random
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
    s1 = dlg_module.s1
    s2 = dlg_module.s2
except Exception as e:
    print(f"Error importing DLG: {e}")
    s1 = ["Searching..."]
    s2 = ["Here are the results."]


# M A I N  C O D E

def search_manual(text):
    """Search within the current YouTube window."""
    ui.press("/")
    ui.write(text)
    s12 = random.choice(s1)
    speak(s12)
    time.sleep(0.5)
    ui.press("enter")
    s12 = random.choice(s2)
    speak(s12)
