"""
JARVIS AI — Centralized Configuration
Handles environment variables, dynamic path resolution, and shared module loading.
"""

import os
import sys
import importlib.util
from dotenv import load_dotenv

# ── Path Resolution ──────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ensure project root is in sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env from project root
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ── Environment Variables ────────────────────────────────────────────────────
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY', '')
WEATHER_CITY = os.environ.get('WEATHER_CITY', 'New Delhi, India')
USER_NAME = os.environ.get('JARVIS_USER_NAME', 'Sir')
ASSISTANT_NAME = os.environ.get('JARVIS_NAME', 'Jarvis')

# ── LLM Configuration ────────────────────────────────────────────────────────
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'auto').lower().strip()  # auto, openai, gemini, ollama, groq
LLM_MODEL = os.environ.get('LLM_MODEL', '').strip()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '').strip()
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '').strip()
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434').strip()
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3:latest').strip()
LLM_TEMPERATURE = float(os.environ.get('LLM_TEMPERATURE', '0.7'))
LLM_MAX_TOKENS = int(os.environ.get('LLM_MAX_TOKENS', '512'))
LLM_ROUTING_MODE = os.environ.get('LLM_ROUTING_MODE', 'hybrid').lower().strip()  # hybrid, fast_first, llm_only, offline_only

# ── Memory & Safety Configuration ────────────────────────────────────────────
MEMORY_DB_PATH = os.environ.get('MEMORY_DB_PATH', os.path.join(PROJECT_ROOT, 'DATA', 'jarvis_memory.db'))
MAX_CONTEXT_TURNS = int(os.environ.get('MAX_CONTEXT_TURNS', '10'))
CONFIRMATION_MODE = os.environ.get('CONFIRMATION_MODE', 'ask_high_risk').lower().strip()  # ask_high_risk, strict, auto_allow

# ── Computer Vision & Computer Control Configuration ─────────────────────────
ENABLE_SCREEN_CAPTURE = os.environ.get('ENABLE_SCREEN_CAPTURE', 'true').lower() in ('true', '1', 'yes')
MAX_COMPUTER_ACTIONS = int(os.environ.get('MAX_COMPUTER_ACTIONS', '20'))
MAX_COMPUTER_RETRIES = int(os.environ.get('MAX_COMPUTER_RETRIES', '3'))
MAX_COMPUTER_DURATION = float(os.environ.get('MAX_COMPUTER_DURATION', '60.0'))
VISION_CONFIDENCE_THRESHOLD = float(os.environ.get('VISION_CONFIDENCE_THRESHOLD', '0.60'))
VISION_PROVIDER = os.environ.get('VISION_PROVIDER', 'auto').lower().strip()
EMERGENCY_STOP_KEY = os.environ.get('EMERGENCY_STOP_KEY', 'esc').strip().lower()

# ── Voice Configuration ──────────────────────────────────────────────────────
WAKE_WORDS = [w.strip().lower() for w in os.environ.get('WAKE_WORDS', 'jarvis,hey jarvis,ok jarvis,okay jarvis,hello jarvis').split(',') if w.strip()]
TTS_VOICE_RATE = int(os.environ.get('TTS_VOICE_RATE', '180'))
TTS_VOICE_VOLUME = float(os.environ.get('TTS_VOICE_VOLUME', '1.0'))
ENABLE_STREAMING = os.environ.get('ENABLE_STREAMING', 'true').lower() in ('true', '1', 'yes')

# ── Common Paths ─────────────────────────────────────────────────────────────
PATHS = {
    'speak': os.path.join(PROJECT_ROOT, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py'),
    'listen': os.path.join(PROJECT_ROOT, 'FUNCTION', 'JARVIS_LISTEN', 'listen.py'),
    'voice_engine': os.path.join(PROJECT_ROOT, 'VOICE', 'voice_engine.py'),
    'dlg': os.path.join(PROJECT_ROOT, 'DATA', 'DLG.py'),
    'brain1': os.path.join(PROJECT_ROOT, 'BRAIN', 'MAIN_BRAIN', 'brain1.py'),
    'agent_brain': os.path.join(PROJECT_ROOT, 'BRAIN', 'CORE_AGENT', 'agent_brain.py'),
    'system_prompt': os.path.join(PROJECT_ROOT, 'BRAIN', 'PROMPTS', 'system_prompt.py'),
    'provider_manager': os.path.join(PROJECT_ROOT, 'BRAIN', 'LLM', 'provider_manager.py'),
    'tool_registry': os.path.join(PROJECT_ROOT, 'BRAIN', 'TOOLS', 'tool_registry.py'),
    'safety_manager': os.path.join(PROJECT_ROOT, 'BRAIN', 'TOOLS', 'safety_manager.py'),
    'conversation_manager': os.path.join(PROJECT_ROOT, 'BRAIN', 'MEMORY', 'conversation_manager.py'),
    'memory_manager': os.path.join(PROJECT_ROOT, 'BRAIN', 'MEMORY', 'memory_manager.py'),
    'qna_txt': os.path.join(PROJECT_ROOT, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.txt'),
    'qna_json': os.path.join(PROJECT_ROOT, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.json'),
    'automations_db': os.path.join(PROJECT_ROOT, 'DATA', 'automations.json'),
    'automation_logs': os.path.join(PROJECT_ROOT, 'DATA', 'automation_logs.json'),
    'automation_manager': os.path.join(PROJECT_ROOT, 'AUTOMATION', 'automation_manager.py'),
    'automation_integration': os.path.join(PROJECT_ROOT, 'AUTOMATION', 'MAIN_INTREGATION', 'automation_intregation.py'),
    'modal_1': os.path.join(PROJECT_ROOT, 'BRAIN', 'TRANING BRAIN', 'MODAL_1', 'modal_1.py'),
    'modal_2': os.path.join(PROJECT_ROOT, 'BRAIN', 'TRANING BRAIN', 'MODAL_2', 'modal_2.py'),
}

# ── Module Loader ────────────────────────────────────────────────────────────
def import_module_from_path(module_name, file_path):
    """Dynamically import a Python module from an absolute file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Module file not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load specification for module at: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

