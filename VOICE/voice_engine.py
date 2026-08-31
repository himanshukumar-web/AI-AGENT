"""
JARVIS AI — Voice Engine & Audio Provider Layer
Provides thread-safe, interruptible TTS with sentence streaming and barge-in capability.
"""

import queue
import threading
import time
from typing import Optional
from colorama import Fore
import pyttsx3

from config import TTS_VOICE_RATE, TTS_VOICE_VOLUME


class VoiceEngine:
    """Thread-safe, non-blocking, interruptible Text-to-Speech Engine."""

    def __init__(self):
        self._lock = threading.Lock()
        self._speech_queue = queue.Queue()
        self._is_speaking = False
        self._stop_requested = False
        self._rate = TTS_VOICE_RATE
        self._volume = TTS_VOICE_VOLUME
        self._worker_thread = None
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        """Initialize pyttsx3 backend."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self._rate)
            self._engine.setProperty('volume', self._volume)
            voices = self._engine.getProperty('voices')
            if len(voices) > 1:
                self._engine.setProperty('voice', voices[1].id)
            elif voices:
                self._engine.setProperty('voice', voices[0].id)
        except Exception as e:
            self._engine = None

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop_speaking(self):
        """Interrupt and stop current speech immediately (Barge-in support)."""
        self._stop_requested = True
        try:
            if self._engine:
                self._engine.stop()
        except Exception:
            pass

    def speak(self, text: str, block: bool = True):
        """
        Convert text to speech.
        If block is True, waits until speech is finished.
        If block is False, dispatches asynchronously.
        """
        if not text or not str(text).strip():
            return

        clean_text = str(text).strip()
        print(Fore.CYAN + f"JARVIS: {clean_text}")

        if not self._engine:
            return

        self._stop_requested = False

        if block:
            self._speak_sync(clean_text)
        else:
            threading.Thread(target=self._speak_sync, args=(clean_text,), daemon=True).start()

    def _speak_sync(self, text: str):
        """Synchronous speech execution with lock."""
        with self._lock:
            if self._stop_requested:
                return
            self._is_speaking = True
            try:
                if self._engine:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception:
                pass
            finally:
                self._is_speaking = False


# Global singleton instance
voice_engine = VoiceEngine()
