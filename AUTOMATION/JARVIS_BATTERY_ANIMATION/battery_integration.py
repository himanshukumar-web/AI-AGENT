"""
JARVIS AI — Battery Integration Module
Central dispatcher for all battery-related commands.
"""

import importlib.util
import os


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current_dir = os.path.dirname(os.path.abspath(__file__))

# Import battery sub-modules using dynamic paths
try:
    battery_alert_module = import_module_from_path(
        'battery_alert', os.path.join(current_dir, 'battery_alert.py'))
    battery_alert = battery_alert_module.battery_alert
    battery_alert1 = battery_alert_module.battery_alert1
except Exception as e:
    print(f"Error importing battery_alert: {e}")
    battery_alert = lambda: None
    battery_alert1 = lambda: None

try:
    battery_plug_module = import_module_from_path(
        'battery_plug_check', os.path.join(current_dir, 'battery_plug_check.py'))
    check_plugin_status1 = battery_plug_module.check_plugin_status1
except Exception as e:
    print(f"Error importing battery_plug_check: {e}")
    check_plugin_status1 = lambda: None

try:
    battery_pct_module = import_module_from_path(
        'check_battery_percentage', os.path.join(current_dir, 'check_battery_percentage.py'))
    battery_percentage = battery_pct_module.battery_percentage
except Exception as e:
    print(f"Error importing check_battery_percentage: {e}")
    battery_percentage = lambda: None


def battery_cmd(text):
    """Route battery-related voice commands."""
    if "battery percentage" in text or "battery level" in text or "how much battery" in text:
        battery_percentage()
        return True
    elif "check plug" in text or "charger status" in text or "is charger" in text:
        check_plugin_status1()
        return True
    elif "battery alert" in text or "battery status" in text:
        battery_alert1()
        return True
    return False
