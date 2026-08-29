import difflib
import random
import webbrowser
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
    websites = dlg_module.websites
    open_dld = dlg_module.open_dld
    success_open = dlg_module.success_open
    open_maybe = dlg_module.open_maybe
    sorry_open = dlg_module.sorry_open
    
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing modules in open_website: {e}")
    websites = {}
    speak = print

# M A I N   C O D E

def openweb(text):

    # Convert the input to lowercase for case-insensitive matching
    website_name_lower = text.lower()

    # Check if the exact website name exists in the dictionary
    if website_name_lower in websites:
        random_dlg = random.choice(open_dld)
        speak(random_dlg + text)
        url = websites[website_name_lower]
        webbrowser.open(url)
        randonsuccess = random.choice(success_open)
        speak(randonsuccess)
    else:
        # Find the closest matching website using string similarity
        matches = difflib.get_close_matches(website_name_lower, websites.keys(), n=1, cutoff=0.6)
        if matches:
            random_dlg = random.choice(open_dld)
            randonopen2 = random.choice(open_maybe)
            closest_match = matches[0]
            speak(randonopen2 + random_dlg + text)
            url = websites[closest_match]
            webbrowser.open(url)
            randonsuccess = random.choice(success_open)
            speak(randonsuccess)
        else:
            randonsorry = random.choice(sorry_open)
            speak(randonsorry +" named " + text)
