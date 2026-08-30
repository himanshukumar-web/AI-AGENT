"""
JARVIS AI — Text-to-Speech Module
Uses pyttsx3 for reliable offline TTS with graceful fallbacks.
"""

import sys
import threading
import pyttsx3
from colorama import Fore, Style, init

init(autoreset=True)

# Initialize the TTS engine
_engine = None
_lock = threading.Lock()


def _get_engine():
    """Lazy-initialize the TTS engine (thread-safe)."""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                try:
                    _engine = pyttsx3.init()
                    _engine.setProperty('rate', 175)     # Speech rate (words per minute)
                    _engine.setProperty('volume', 1.0)   # Volume (0.0 to 1.0)

                    voices = _engine.getProperty('voices')
                    if len(voices) > 1:
                        _engine.setProperty('voice', voices[1].id)
                    elif voices:
                        _engine.setProperty('voice', voices[0].id)
                except Exception as e:
                    print(Fore.YELLOW + f"  [TTS Init Warning] Could not initialize pyttsx3: {e}")
                    _engine = None
    return _engine


def speak(text):
    """Convert text to speech using pyttsx3 (offline, reliable)."""
    if not text or not str(text).strip():
        return

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


if __name__ == "__main__":
    speak("Jarvis text-to-speech system is online and operational.")
    speak("All systems nominal, sir.")
