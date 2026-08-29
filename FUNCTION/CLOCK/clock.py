import datetime
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
    print(f"Error importing speak in clock: {e}")
    speak = print

# M A I N    C O D E

def what_is_the_time():
    try:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")

    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        speak(error_message)
