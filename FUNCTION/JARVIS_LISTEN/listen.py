"""
JARVIS AI — Speech Recognition Module (Voice 3.0)
Supports PyAudio and SoundDevice dual backends for 100% Python 3.14+ compatibility.
Handles English, Hindi, and Hinglish input with intelligent translation and intent normalization.
"""

import io
import re
import time
import wave
import numpy as np
import speech_recognition as sr
from mtranslate import translate
from colorama import Fore, Style, init

init(autoreset=True)

# Check sounddevice availability
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

# Check PyAudio availability
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

# Import wake words safely
try:
    from config import WAKE_WORDS
except Exception:
    WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis", "okay jarvis", "hello jarvis"]

# Common Hinglish phrase mappings for direct conversational intent normalization
HINGLISH_INTENT_MAP = {
    r"\bmujhe mausam batao\b": "tell me the weather",
    r"\bmausam batao\b": "tell me the weather",
    r"\bmausam kaisa hai\b": "how is the weather",
    r"\bweather kaisa hai\b": "how is the weather",
    r"\bkitne baje hain\b": "what time is it",
    r"\btime kya hua\b": "what time is it",
    r"\bbattery kitni hai\b": "what is the battery percentage",
    r"\bchup ho jao\b": "stop",
    r"\bshant ho jao\b": "stop",
    r"\bsearch karo\b": "search for",
    r"\bchala do\b": "play",
    r"\bband karo\b": "close",
    r"\bmujhe batao\b": "tell me",
    r"\byaad rakho\b": "remember",
    r"\bbhool jao\b": "forget",
    r"\bkholo\b": "open",
    r"\bchalao\b": "play",
    r"\broko\b": "stop",
    r"\bruko\b": "stop",
    r"\bchup\b": "stop",
    r"\bbatao\b": "tell me",
    r"\bdhoondho\b": "search for",
}

INTERRUPT_PHRASES = [
    "stop", "jarvis stop", "cancel", "stop now", "abort",
    "chup", "ruko", "roko", "shut up", "quiet", "silence", "stop speaking"
]


def is_interruption_phrase(text: str) -> bool:
    """Check if the spoken phrase is a stop or cancellation command."""
    if not text:
        return False
    t = text.lower().strip()
    return t in INTERRUPT_PHRASES or any(t.startswith(ip + " ") or t == ip for ip in INTERRUPT_PHRASES)


def normalize_hinglish(text: str) -> str:
    """Normalize common Hinglish conversational terms to English intents."""
    if not text:
        return ""
    norm = text.lower().strip()
    for pattern in sorted(HINGLISH_INTENT_MAP.keys(), key=len, reverse=True):
        repl = HINGLISH_INTENT_MAP[pattern]
        norm = re.sub(pattern, repl, norm, flags=re.IGNORECASE)
    norm = re.sub(r'\s+', ' ', norm).strip()
    return norm



def Trans_hindi_to_english(txt: str) -> str:
    """Translate Hindi/Hinglish voice input to English with fallback."""
    if not txt:
        return ""
    # First apply direct Hinglish normalization
    normalized = normalize_hinglish(txt)
    # Check if text contains Devanagari Unicode range
    has_hindi_chars = any('\u0900' <= char <= '\u097F' for char in txt)
    if has_hindi_chars:
        try:
            english_txt = translate(txt, "en-us")
            return english_txt if english_txt else normalized
        except Exception:
            return normalized
    return normalized


def _record_with_sounddevice(duration=5, sample_rate=16000):
    """Record audio using sounddevice when PyAudio is not available."""
    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()

        # Check if there is actual audio above silence threshold
        max_amplitude = np.max(np.abs(recording))
        if max_amplitude < 250:  # Silence threshold
            return None

        # Pack into WAV in memory
        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())

        byte_io.seek(0)
        return byte_io
    except Exception:
        return None


def has_wake_word(text: str) -> bool:
    """Check if the recognized voice command contains any configured wake words."""
    if not text:
        return False
    t = text.lower()
    return any(w in t for w in WAKE_WORDS)


def listen() -> str:
    """
    Listen to user voice input.
    Dual-backend: PyAudio microphone or SoundDevice fallback.
    Translates input if in Hindi/Hinglish and returns recognized text.
    """
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6
    recognizer.non_speaking_duration = 0.3

    # Method 1: PyAudio backend
    if HAS_PYAUDIO:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print(Fore.LIGHTGREEN_EX + "  Listening (PyAudio)...", end="\r", flush=True)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print(Fore.LIGHTYELLOW_EX + "  Recognizing speech...", end="\r", flush=True)
                recognized_txt = recognizer.recognize_google(audio, language="en-IN").lower()
                if recognized_txt:
                    translated_txt = Trans_hindi_to_english(recognized_txt)
                    print(Fore.BLUE + f"  User: {translated_txt}")
                    return translated_txt
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception:
            pass  # Fall through to sounddevice

    # Method 2: SoundDevice backend (Native Python 3.14 on Windows)
    if HAS_SOUNDDEVICE:
        try:
            print(Fore.LIGHTGREEN_EX + "  Listening...", end="\r", flush=True)
            wav_bytes = _record_with_sounddevice(duration=4, sample_rate=16000)
            if wav_bytes is not None:
                print(Fore.LIGHTYELLOW_EX + "  Recognizing speech...", end="\r", flush=True)
                with sr.AudioFile(wav_bytes) as source:
                    audio = recognizer.record(source)
                    recognized_txt = recognizer.recognize_google(audio, language="en-IN").lower()
                    if recognized_txt:
                        translated_txt = Trans_hindi_to_english(recognized_txt)
                        print(Fore.BLUE + f"  User: {translated_txt}")
                        return translated_txt
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(Fore.YELLOW + f"  Speech API network error: {e}")
            return ""
        except Exception:
            return ""

    # Method 3: Fallback when neither audio capture is functional
    print(Fore.YELLOW + "  [Audio Warning] No microphone backend available.")
    return ""


def hearing() -> str:
    """Continuous listening helper."""
    return listen()


if __name__ == "__main__":
    print("Testing JARVIS Listening module (Voice 3.0)...")
    test_hinglish = "Jarvis YouTube kholo aur Python tutorials search karo"
    print(f"Sample Hinglish: '{test_hinglish}' -> Normalized: '{Trans_hindi_to_english(test_hinglish)}'")
    result = listen()
    print(f"Recorded Result: '{result}'")


