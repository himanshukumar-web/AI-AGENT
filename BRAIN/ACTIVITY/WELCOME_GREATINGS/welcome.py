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
    welcomedlg = dlg_module.welcomedlg
except Exception as e:
    print(f"Error importing modules in welcome: {e}")
    speak = print
    welcomedlg = ["Welcome sir."]

# M A I N   C O D E
def welcome():
    if welcomedlg:
        welcome_msg = random.choice(welcomedlg)
        speak(welcome_msg)