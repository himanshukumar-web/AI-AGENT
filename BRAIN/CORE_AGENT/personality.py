"""
JARVIS AI — Personality & Tone Customization Engine (Phase 4)
Adjusts conversational tone, voice brevity, and style across multiple personality modes.
"""

from enum import Enum
from typing import Optional


class PersonalityMode(Enum):
    DEFAULT = "default"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONCISE = "concise"
    TECHNICAL = "technical"


class PersonalityEngine:
    """Adapts assistant output style based on configured personality and voice mode."""

    def __init__(self, mode: PersonalityMode = PersonalityMode.CONCISE):
        self.mode = mode

    def set_mode(self, mode_name_or_enum):
        """Set active personality mode."""
        if isinstance(mode_name_or_enum, PersonalityMode):
            self.mode = mode_name_or_enum
        elif isinstance(mode_name_or_enum, str):
            try:
                self.mode = PersonalityMode(mode_name_or_enum.lower())
            except ValueError:
                self.mode = PersonalityMode.DEFAULT

    def format_acknowledgment(self, action_name: str, is_voice: bool = True) -> str:
        """Generate human-like action confirmations."""
        if self.mode == PersonalityMode.CONCISE or is_voice:
            return "Done."
        elif self.mode == PersonalityMode.FRIENDLY:
            return f"Done! {action_name.capitalize()} is ready."
        elif self.mode == PersonalityMode.TECHNICAL:
            return f"Action '{action_name}' executed successfully with status OK."
        elif self.mode == PersonalityMode.PROFESSIONAL:
            return f"{action_name.capitalize()} has been completed."
        return "Done."

    def format_error(self, error_message: str, is_voice: bool = True) -> str:
        """Format errors safely for speech without exposing raw tracebacks."""
        # Sanitize technical stack traces
        clean_err = error_message.split("\n")[-1]
        if "Traceback" in clean_err or "Exception" in clean_err:
            clean_err = "The operation could not be completed at this time."

        if is_voice or self.mode == PersonalityMode.CONCISE:
            return f"I couldn't do that. {clean_err}"
        return f"Operation failed: {clean_err}"

    def detect_language_tone(self, text: str) -> str:
        """Detect language preference: 'hindi', 'hinglish', or 'english'."""
        t = text.lower()
        hindi_indicators = ["kholo", "batao", "suno", "sunao", "karo", "kitni", "kaise", "chup", "ruko", "namaste", "dhanyawad", "shukriya"]
        if any(w in t for w in hindi_indicators):
            return "hinglish"
        return "english"


# Global singleton instance
personality_engine = PersonalityEngine()
