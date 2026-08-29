"""
JARVIS AI — Common Automation Integration
Routes open/close application commands.
"""

import importlib.util
import os


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    common_close_module = import_module_from_path(
        'common_close', os.path.join(current_dir, 'common_close.py'))
    close = common_close_module.close
except Exception as e:
    print(f"Error importing common_close: {e}")
    close = lambda: None

try:
    common_open_module = import_module_from_path(
        'common_open', os.path.join(current_dir, 'common_open.py'))
    open_app = common_open_module.open
except Exception as e:
    print(f"Error importing common_open: {e}")
    open_app = lambda x: None


def common_cmd(text):
    """Route open/close commands."""
    if "open" in text or "kholo" in text:
        app_name = text.replace("open", "").replace("kholo", "").strip()
        if app_name:
            open_app(app_name)
            return True
    elif "close" in text or "band karo" in text or "band kar do" in text:
        close()
        return True
    return False