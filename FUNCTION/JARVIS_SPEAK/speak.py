"""
JARVIS AI — Text-to-Speech Module
Uses pyttsx3 for reliable offline TTS instead of fragile web scraping.
"""

import pyttsx3
import threading

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
                    # Configure voice properties
                    _engine.setProperty('rate', 175)     # Speech rate (words per minute)
                    _engine.setProperty('volume', 1.0)   # Volume (0.0 to 1.0)
                    
                    # Try to set a clear voice
                    voices = _engine.getProperty('voices')
                    if len(voices) > 1:
                        # Use the second voice (usually female/clearer) if available
                        _engine.setProperty('voice', voices[1].id)
                    elif voices:
                        _engine.setProperty('voice', voices[0].id)
                except Exception as e:
                    print(f"Error initializing TTS engine: {e}")
                    return None
    return _engine


def speak(text):
    """Convert text to speech using pyttsx3 (offline, reliable)."""
    if not text:
        return

    try:
        engine = _get_engine()
        if engine:
            print(f"JARVIS: {text}")
            engine.say(str(text))
            engine.runAndWait()
        else:
            # Fallback: just print if TTS fails
            print(f"JARVIS (TTS offline): {text}")
    except Exception as e:
        print(f"TTS Error: {e}")
        print(f"JARVIS (fallback): {text}")


if __name__ == "__main__":
    speak("Jarvis text-to-speech system is online and operational.")
    speak("All systems nominal, sir.")
