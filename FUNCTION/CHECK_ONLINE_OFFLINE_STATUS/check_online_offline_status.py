import requests # pip install requests
import importlib.util
import os

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak in check_online_offline_status: {e}")
    speak = print

# M A I N    C O D E

def is_online(url="http://www.google.com", timeout=5):
    try:
        # Try to make a GET request to the specified URL
        response = requests.get(url, timeout=timeout)
        # Check if the response status code is in the success range (200-299)
        return response.status_code >= 200 and response.status_code < 300
    except requests.ConnectionError:
        return False

# Example usage
def internet_status():
    if is_online():
        x = "YES SIR ! I AM READY AND ONLINE"
        speak(x)
    else:
        x = "HEY THERE SIR ! I AM FRIDAY , SORRY BUT JARVIS IS CURRENTLY NOT ONLINE"
        print(x)
