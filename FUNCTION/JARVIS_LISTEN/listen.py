"""
JARVIS AI — Speech Recognition Module
Supports PyAudio and SoundDevice dual backends for 100% Python 3.14+ compatibility.
Handles English & Hindi input with automatic translation.
"""

import io
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


def Trans_hindi_to_english(txt):
    """Translate Hindi voice input to English."""
    if not txt:
        return ""
    try:
        english_txt = translate(txt, "en-us")
        return english_txt
    except Exception as e:
        return txt


def _record_with_sounddevice(duration=5, sample_rate=16000):
    """Record audio using sounddevice when PyAudio is not available."""
    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        
        # Check if there is actual audio above silence threshold
        max_amplitude = np.max(np.abs(recording))
        if max_amplitude < 300:  # Silence threshold
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
    except Exception as e:
        return None


# Import wake words safely
try:
    from config import WAKE_WORDS
except Exception:
    WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis", "okay jarvis"]


def has_wake_word(text: str) -> bool:
    """Check if the recognized voice command contains any configured wake words."""
    if not text:
        return False
    t = text.lower()
    return any(w in t for w in WAKE_WORDS)


def listen():
    """
    Listen to user voice input.
    Dual-backend: PyAudio microphone or SoundDevice fallback.
    Translates input if in Hindi and returns recognized text.
    """
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6
    recognizer.non_speaking_duration = 0.3

    # Method 1: PyAudio backend
    if HAS_PYAUDIO:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                print(Fore.LIGHTGREEN_EX + "  Listening (PyAudio)...", end="\r", flush=True)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
                print(Fore.LIGHTYELLOW_EX + "  Recognizing speech...", end="\r", flush=True)
                recognized_txt = recognizer.recognize_google(audio).lower()
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
                    recognized_txt = recognizer.recognize_google(audio).lower()
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


def hearing():
    """Continuous listening helper."""
    return listen()


if __name__ == "__main__":
    print("Testing JARVIS Listening module...")
    result = listen()
    print(f"Result: '{result}'")

