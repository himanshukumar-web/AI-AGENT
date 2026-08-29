"""
JARVIS AI — Automation Manager
Manages custom automations: create, edit, delete, enable/disable, execute, schedule.
Stores automations in a JSON file for persistence.
"""

import json
import os
import uuid
import datetime
import threading
import webbrowser
import importlib.util

try:
    import schedule
except ImportError:
    schedule = None


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Path Resolution ──────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))

AUTOMATIONS_FILE = os.path.join(project_root, 'DATA', 'automations.json')
LOGS_FILE = os.path.join(project_root, 'DATA', 'automation_logs.json')

# Load speak
speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak in automation_manager: {e}")
    speak = print


# ── Allowed Actions ──────────────────────────────────────────────────────────
# Only these actions are permitted (security: no arbitrary command execution)
ALLOWED_ACTIONS = {
    'open_website': 'Open a website URL in the default browser',
    'open_app': 'Open an application using Windows search',
    'search_google': 'Search a query on Google',
    'search_youtube': 'Search a query on YouTube',
    'play_music': 'Play a song on YouTube',
    'speak_text': 'Speak a custom text message',
    'check_weather': 'Check the current weather',
    'check_time': 'Tell the current time',
    'check_battery': 'Check battery percentage',
    'check_ip': 'Find the public IP address',
    'check_speed': 'Check internet speed',
    'get_joke': 'Tell a random joke',
    'get_advice': 'Give a random piece of advice',
}


# ── Storage ──────────────────────────────────────────────────────────────────
def _load_automations():
    """Load automations from JSON file."""
    if os.path.exists(AUTOMATIONS_FILE):
        try:
            with open(AUTOMATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_automations(automations):
    """Save automations to JSON file."""
    os.makedirs(os.path.dirname(AUTOMATIONS_FILE), exist_ok=True)
    with open(AUTOMATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(automations, f, indent=2, default=str)


def _log_execution(automation_id, name, status, message=""):
    """Log an automation execution event."""
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'automation_id': automation_id,
        'name': name,
        'status': status,
        'message': message
    }

    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []

    logs.append(log_entry)
    # Keep only last 100 entries
    logs = logs[-100:]

    os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, default=str)


# ── CRUD Operations ──────────────────────────────────────────────────────────
def create_automation(name, action, parameters=None, schedule_time=None):
    """Create a new automation.

    Args:
        name: Human-readable name for this automation
        action: One of ALLOWED_ACTIONS keys
        parameters: Dict of parameters for the action
        schedule_time: Optional HH:MM string for daily scheduling
    
    Returns:
        The created automation dict, or None if invalid
    """
    if action not in ALLOWED_ACTIONS:
        speak(f"Invalid action: {action}. Allowed actions are: {', '.join(ALLOWED_ACTIONS.keys())}")
        return None

    automation = {
        'id': str(uuid.uuid4())[:8],
        'name': name,
        'action': action,
        'parameters': parameters or {},
        'enabled': True,
        'schedule_time': schedule_time,
        'created_at': datetime.datetime.now().isoformat(),
        'last_run': None,
        'run_count': 0,
    }

    automations = _load_automations()
    automations.append(automation)
    _save_automations(automations)

    speak(f"Automation '{name}' created successfully.")
    return automation


def list_automations():
    """List all automations and speak a summary."""
    automations = _load_automations()
    if not automations:
        speak("You have no automations configured.")
        return []

    speak(f"You have {len(automations)} automation{'s' if len(automations) != 1 else ''}.")
    for auto in automations:
        status = "enabled" if auto.get('enabled', True) else "disabled"
        speak(f"{auto['name']}: {ALLOWED_ACTIONS.get(auto['action'], auto['action'])}. Status: {status}.")
    return automations


def get_automation(automation_id):
    """Get a specific automation by ID."""
    automations = _load_automations()
    for auto in automations:
        if auto['id'] == automation_id:
            return auto
    return None


def edit_automation(automation_id, **updates):
    """Edit an automation's properties."""
    automations = _load_automations()
    for i, auto in enumerate(automations):
        if auto['id'] == automation_id:
            for key, value in updates.items():
                if key in ('name', 'action', 'parameters', 'schedule_time', 'enabled'):
                    if key == 'action' and value not in ALLOWED_ACTIONS:
                        speak(f"Invalid action: {value}")
                        return None
                    automations[i][key] = value
            _save_automations(automations)
            speak(f"Automation '{auto['name']}' updated successfully.")
            return automations[i]
    speak("Automation not found.")
    return None


def delete_automation(automation_id):
    """Delete an automation by ID."""
    automations = _load_automations()
    for i, auto in enumerate(automations):
        if auto['id'] == automation_id:
            name = auto['name']
            automations.pop(i)
            _save_automations(automations)
            speak(f"Automation '{name}' deleted successfully.")
            return True
    speak("Automation not found.")
    return False


def enable_automation(automation_id):
    """Enable an automation."""
    return edit_automation(automation_id, enabled=True)


def disable_automation(automation_id):
    """Disable an automation."""
    return edit_automation(automation_id, enabled=False)


def get_automation_history():
    """Get execution logs."""
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                if not logs:
                    speak("No automation history found.")
                else:
                    speak(f"Found {len(logs)} execution records.")
                    # Speak last 3
                    for log in logs[-3:]:
                        speak(f"{log['name']}: {log['status']} at {log['timestamp'][:16]}")
                return logs
        except (json.JSONDecodeError, IOError):
            pass
    speak("No automation history found.")
    return []


# ── Execution Engine ─────────────────────────────────────────────────────────
def execute_automation(automation_id):
    """Execute a specific automation by ID."""
    auto = get_automation(automation_id)
    if not auto:
        speak("Automation not found.")
        return False

    if not auto.get('enabled', True):
        speak(f"Automation '{auto['name']}' is disabled.")
        return False

    return _run_action(auto)


def execute_automation_by_name(name):
    """Execute an automation by its name (fuzzy match)."""
    automations = _load_automations()
    name_lower = name.lower().strip()

    for auto in automations:
        if auto['name'].lower() == name_lower:
            if not auto.get('enabled', True):
                speak(f"Automation '{auto['name']}' is disabled.")
                return False
            return _run_action(auto)

    # Try partial match
    for auto in automations:
        if name_lower in auto['name'].lower():
            if not auto.get('enabled', True):
                speak(f"Automation '{auto['name']}' is disabled.")
                return False
            return _run_action(auto)

    speak(f"No automation found matching '{name}'.")
    return False


def _run_action(automation):
    """Execute the action defined in an automation."""
    action = automation['action']
    params = automation.get('parameters', {})
    name = automation['name']

    try:
        if action == 'open_website':
            url = params.get('url', '')
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                speak(f"Opening {url}")
                webbrowser.open(url)
            else:
                speak("No URL specified for this automation.")
                _log_execution(automation['id'], name, 'failed', 'No URL specified')
                return False

        elif action == 'open_app':
            app_name = params.get('app_name', '')
            if app_name:
                try:
                    open_mod = import_module_from_path(
                        'common_open',
                        os.path.join(project_root, 'AUTOMATION', 'JARVIS_COMMON_AUTOMATION', 'common_open.py'))
                    open_mod.open(app_name)
                except Exception as e:
                    speak(f"Error opening {app_name}: {e}")
                    _log_execution(automation['id'], name, 'failed', str(e))
                    return False
            else:
                speak("No app name specified.")
                return False

        elif action == 'search_google':
            query = params.get('query', '')
            if query:
                try:
                    import pywhatkit
                    speak(f"Searching Google for {query}")
                    pywhatkit.search(query)
                except Exception as e:
                    speak(f"Error searching Google: {e}")
                    return False
            else:
                speak("No search query specified.")
                return False

        elif action == 'search_youtube':
            query = params.get('query', '')
            if query:
                speak(f"Searching YouTube for {query}")
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            else:
                speak("No search query specified.")
                return False

        elif action == 'play_music':
            song = params.get('song', '')
            if song:
                try:
                    play_mod = import_module_from_path(
                        'play_music_in_youtube',
                        os.path.join(project_root, 'AUTOMATION', 'JARVIS_YOUTUBE_AUTOMATION', 'play_music_in_youtube.py'))
                    play_mod.play_music_on_youtube(song)
                except Exception as e:
                    speak(f"Error playing music: {e}")
                    return False
            else:
                speak("No song specified.")
                return False

        elif action == 'speak_text':
            text = params.get('text', '')
            if text:
                speak(text)
            else:
                speak("No text specified.")
                return False

        elif action == 'check_weather':
            try:
                temp_mod = import_module_from_path(
                    'temp',
                    os.path.join(project_root, 'FUNCTION', 'CHECK_TEMPEATURE', 'temp.py'))
                city = params.get('city', None)
                temp_mod.Temp(city)
            except Exception as e:
                speak(f"Error checking weather: {e}")
                return False

        elif action == 'check_time':
            try:
                clock_mod = import_module_from_path(
                    'clock',
                    os.path.join(project_root, 'FUNCTION', 'CLOCK', 'clock.py'))
                clock_mod.what_is_the_time()
            except Exception as e:
                speak(f"Error checking time: {e}")
                return False

        elif action == 'check_battery':
            try:
                bat_mod = import_module_from_path(
                    'check_battery_percentage',
                    os.path.join(project_root, 'AUTOMATION', 'JARVIS_BATTERY_ANIMATION', 'check_battery_percentage.py'))
                bat_mod.battery_percentage()
            except Exception as e:
                speak(f"Error checking battery: {e}")
                return False

        elif action == 'check_ip':
            try:
                ip_mod = import_module_from_path(
                    'find_my_ip',
                    os.path.join(project_root, 'FUNCTION', 'FIND_MY_IP', 'find_my_ip.py'))
                ip = ip_mod.find_my_ip()
                speak(f"Your public IP address is {ip}")
            except Exception as e:
                speak(f"Error finding IP: {e}")
                return False

        elif action == 'check_speed':
            try:
                speed_mod = import_module_from_path(
                    'check_internet_speed',
                    os.path.join(project_root, 'FUNCTION', 'CHECK_INTERNET_SPEED', 'check_internet_speed.py'))
                speed_mod.check_internet_speed()
            except Exception as e:
                speak(f"Error checking speed: {e}")
                return False

        elif action == 'get_joke':
            try:
                joke_mod = import_module_from_path(
                    'joke',
                    os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'JOKE', 'joke.py'))
                joke = joke_mod.get_random_joke()
                speak(joke)
            except Exception as e:
                speak(f"Error getting joke: {e}")
                return False

        elif action == 'get_advice':
            try:
                advice_mod = import_module_from_path(
                    'advice',
                    os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'ADVICE', 'advice.py'))
                advice = advice_mod.get_random_advice()
                speak(advice)
            except Exception as e:
                speak(f"Error getting advice: {e}")
                return False

        else:
            speak(f"Unknown action: {action}")
            _log_execution(automation['id'], name, 'failed', f'Unknown action: {action}')
            return False

        # Update automation run stats
        _update_run_stats(automation['id'])
        _log_execution(automation['id'], name, 'success')
        return True

    except Exception as e:
        _log_execution(automation['id'], name, 'failed', str(e))
        speak(f"Automation '{name}' failed: {e}")
        return False


def _update_run_stats(automation_id):
    """Update the last_run time and run_count."""
    automations = _load_automations()
    for i, auto in enumerate(automations):
        if auto['id'] == automation_id:
            automations[i]['last_run'] = datetime.datetime.now().isoformat()
            automations[i]['run_count'] = auto.get('run_count', 0) + 1
            _save_automations(automations)
            return


# ── Scheduler ────────────────────────────────────────────────────────────────
_scheduler_thread = None
_scheduler_running = False


def start_scheduler():
    """Start the background scheduler for scheduled automations."""
    global _scheduler_thread, _scheduler_running

    if schedule is None:
        print("Schedule library not installed. Scheduled automations are disabled.")
        return

    if _scheduler_running:
        return

    def _scheduler_loop():
        global _scheduler_running
        _scheduler_running = True
        import time
        while _scheduler_running:
            schedule.run_pending()
            time.sleep(30)

    # Set up scheduled automations
    _setup_scheduled_jobs()

    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler_running
    _scheduler_running = False


def _setup_scheduled_jobs():
    """Read automations and set up scheduled jobs."""
    if schedule is None:
        return

    schedule.clear()
    automations = _load_automations()

    for auto in automations:
        if auto.get('enabled', True) and auto.get('schedule_time'):
            try:
                schedule.every().day.at(auto['schedule_time']).do(
                    _run_action, auto
                )
            except Exception as e:
                print(f"Error scheduling '{auto['name']}': {e}")


# ── Voice Command Interface ──────────────────────────────────────────────────
def handle_automation_command(text):
    """Handle automation-related voice commands.
    
    Returns True if command was handled, False otherwise.
    """
    text_lower = text.lower().strip()

    if "list automation" in text_lower or "show automation" in text_lower or "my automation" in text_lower:
        list_automations()
        return True

    elif "automation history" in text_lower or "automation log" in text_lower:
        get_automation_history()
        return True

    elif "run automation" in text_lower or "execute automation" in text_lower:
        name = text_lower.replace("run automation", "").replace("execute automation", "").strip()
        if name:
            execute_automation_by_name(name)
        else:
            speak("Please specify which automation to run.")
        return True

    elif "delete automation" in text_lower or "remove automation" in text_lower:
        name = text_lower.replace("delete automation", "").replace("remove automation", "").strip()
        if name:
            automations = _load_automations()
            for auto in automations:
                if name in auto['name'].lower():
                    delete_automation(auto['id'])
                    return True
            speak(f"No automation found matching '{name}'.")
        else:
            speak("Please specify which automation to delete.")
        return True

    elif "enable automation" in text_lower:
        name = text_lower.replace("enable automation", "").strip()
        if name:
            automations = _load_automations()
            for auto in automations:
                if name in auto['name'].lower():
                    enable_automation(auto['id'])
                    return True
            speak(f"No automation found matching '{name}'.")
        return True

    elif "disable automation" in text_lower:
        name = text_lower.replace("disable automation", "").strip()
        if name:
            automations = _load_automations()
            for auto in automations:
                if name in auto['name'].lower():
                    disable_automation(auto['id'])
                    return True
            speak(f"No automation found matching '{name}'.")
        return True

    elif "create automation" in text_lower or "new automation" in text_lower:
        speak("To create an automation, please use the command format: "
              "create automation named [name] action [action_type] with [parameters].")
        speak(f"Available actions are: {', '.join(ALLOWED_ACTIONS.keys())}")
        return True

    return False
