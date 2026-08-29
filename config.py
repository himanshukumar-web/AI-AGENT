"""
JARVIS AI — Centralized Configuration
Handles environment variables, dynamic path resolution, and shared module loading.
"""

import os
import importlib.util
from dotenv import load_dotenv

# ── Path Resolution ──────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Load .env from project root
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ── Environment Variables ────────────────────────────────────────────────────
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY', '')
WEATHER_CITY = os.environ.get('WEATHER_CITY', 'New Delhi, India')
USER_NAME = os.environ.get('JARVIS_USER_NAME', 'Sir')

# ── Common Paths ─────────────────────────────────────────────────────────────
PATHS = {
    'speak': os.path.join(PROJECT_ROOT, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py'),
    'listen': os.path.join(PROJECT_ROOT, 'FUNCTION', 'JARVIS_LISTEN', 'listen.py'),
    'dlg': os.path.join(PROJECT_ROOT, 'DATA', 'DLG.py'),
    'brain1': os.path.join(PROJECT_ROOT, 'BRAIN', 'MAIN_BRAIN', 'brain1.py'),
    'qna_txt': os.path.join(PROJECT_ROOT, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.txt'),
    'qna_json': os.path.join(PROJECT_ROOT, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.json'),
    'automations_db': os.path.join(PROJECT_ROOT, 'DATA', 'automations.json'),
    'automation_logs': os.path.join(PROJECT_ROOT, 'DATA', 'automation_logs.json'),
}

# ── Module Loader ────────────────────────────────────────────────────────────
def import_module_from_path(module_name, file_path):
    """Dynamically import a Python module from an absolute file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Module file not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
