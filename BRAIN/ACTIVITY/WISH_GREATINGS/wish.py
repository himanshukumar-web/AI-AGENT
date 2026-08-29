from datetime import date
import datetime
import random
import importlib.util
import os

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
dlg_path = os.path.join(project_root, 'DATA', 'DLG.py')

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
    
    dlg_module = import_module_from_path('DLG', dlg_path)
    good_morningdlg = dlg_module.good_morningdlg
    good_afternoondlg = dlg_module.good_afternoondlg
    good_eveningdlg = dlg_module.good_eveningdlg
    good_nightdlg = dlg_module.good_nightdlg
except Exception as e:
    print(f"Error importing modules in wish: {e}")
    speak = print
    good_morningdlg = ["Good morning"]
    good_afternoondlg = ["Good afternoon"]
    good_eveningdlg = ["Good evening"]
    good_nightdlg = ["Good night"]

# M A I N   C O D E
today = date.today()
formatted_date = today.strftime("%d %b %y")

def wish():
    nowx = datetime.datetime.now()
    current_hour = nowx.hour
    if 5 <= current_hour < 12:
        if good_morningdlg:
            gd_dlg = random.choice(good_morningdlg)
            speak(gd_dlg)
    elif 12 <= current_hour < 17:
        if good_afternoondlg:
            ga_dlg = random.choice(good_afternoondlg)
            speak(ga_dlg)
    elif 17 <= current_hour < 21:
        if good_eveningdlg:
            ge_dlg = random.choice(good_eveningdlg)
            speak(ge_dlg)
    else:
        if good_nightdlg:
            gn_dlg = random.choice(good_nightdlg)
            speak(gn_dlg)


def Greating(text):
    if "good morning" in text or "good afternoon" in text or "good evening" in text or "good night" in text:
        wish()
    else:
        pass