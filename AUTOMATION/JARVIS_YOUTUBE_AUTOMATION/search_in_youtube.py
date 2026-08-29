import random
import pyautogui as ui
import webbrowser
import time
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
    yt_search = dlg_module.yt_search
    s1 = dlg_module.s1
    s2 = dlg_module.s2
    
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing modules in search_in_youtube: {e}")
    yt_search = ["Searching YouTube..."]
    s1 = ["Searching..."]
    s2 = ["Here are the results."]
    speak = print

#main code

def youtube_search(text):
    dlg = random.choice(yt_search)
    speak(dlg)
    webbrowser.open("https://www.youtube.com//")
    time.sleep(2)
    ui.press("/")
    ui.write(text)
    s12 = random.choice(s1)
    speak( s12 ) 
    time.sleep(0.5)
    ui.press("enter")
    s12 = random.choice(s2)
    speak(s12)
