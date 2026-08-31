"""
JARVIS AI — Text-to-Speech Module
Uses pyttsx3 for reliable offline TTS with graceful fallbacks.
"""

import sys
import threading
import pyttsx3
from colorama import Fore, Style, init

init(autoreset=True)

# ── Modern Voice Engine Integration ──────────────────────────────────────────
try:
    from VOICE.voice_engine import voice_engine
    HAS_VOICE_ENGINE = True
except Exception:
    HAS_VOICE_ENGINE = False

# Initialize fallback engine
_engine = None
_lock = threading.Lock()


def _get_engine():
    """Lazy-initialize the TTS engine (thread-safe fallback)."""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                try:
                    _engine = pyttsx3.init()
                    _engine.setProperty('rate', 180)
                    _engine.setProperty('volume', 1.0)
                    voices = _engine.getProperty('voices')
                    if len(voices) > 1:
                        _engine.setProperty('voice', voices[1].id)
                    elif voices:
                        _engine.setProperty('voice', voices[0].id)
                except Exception:
                    _engine = None
    return _engine


def speak(text, block=True):
    """Convert text to speech using VoiceEngine with reliable offline pyttsx3 fallback."""
    if not text or not str(text).strip():
        return

    if HAS_VOICE_ENGINE:
        try:
            voice_engine.speak(text, block=block)
            return
        except Exception:
            pass

    text_str = str(text).strip()
    print(Fore.CYAN + f"JARVIS: {text_str}")

    try:
        engine = _get_engine()
        if engine is not None:
            with _lock:
                engine.say(text_str)
                engine.runAndWait()
    except Exception as e:
        print(Fore.YELLOW + f"  [TTS Playback Warning]: {e}")


def stop_speaking():
    """Interrupt ongoing speech."""
    if HAS_VOICE_ENGINE:
        voice_engine.stop_speaking()


if __name__ == "__main__":
    speak("Jarvis text-to-speech system is online and operational.")

