"""
JARVIS AI — Play Music on YouTube
Uses pywhatkit to play a song on YouTube.
"""

import time
import pywhatkit as kt
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
    playsong = dlg_module.playsong
    playing_dlg = dlg_module.playing_dlg
except Exception as e:
    print(f"Error importing DLG: {e}")
    playsong = ["Playing your song now."]
    playing_dlg = ["Now playing."]


# M A I N  C O D E

def play_music_on_youtube(text):
    """Play a song on YouTube using pywhatkit."""
    playdlg = random.choice(playsong)
    speak(playdlg)
    try:
        kt.playonyt(text)
        time.sleep(3)
        playdlg = random.choice(playing_dlg)
        speak(playdlg + " " + text)
    except Exception as e:
        print(f"Error playing on YouTube: {e}")
        speak("Sorry sir, I was unable to play that on YouTube.")
