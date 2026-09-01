"""
JARVIS AI — Centralized Confirmation Center (Phase 4)
Handles confirmation gates for medium/high-risk tool executions across Voice and CLI.
"""

from typing import Any, Dict, Optional
from BRAIN.TOOLS.safety_manager import safety_manager, RiskLevel
from colorama import Fore, Style, init

init(autoreset=True)


class ConfirmationCenter:
    """Provides a single centralized confirmation interface for safety-gated operations."""

    def __init__(self):
        pass

    def requires_confirmation(self, tool_name: str) -> bool:
        """Check if tool requires user confirmation based on risk policy."""
        return safety_manager.should_confirm(tool_name)

    def request_confirmation_cli(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """Prompt user on CLI for confirmation."""
        args_str = f" with {arguments}" if arguments else ""
        prompt = Fore.YELLOW + f"[CONFIRMATION REQUIRED] Execute high-risk tool '{tool_name}'{args_str}? [y/N]: " + Style.RESET_ALL
        try:
            choice = input(prompt).strip().lower()
            return choice in ["y", "yes", "confirm", "do it"]
        except (EOFError, KeyboardInterrupt):
            return False

    def request_confirmation_voice(self, tool_name: str) -> bool:
        """Prompt user via voice for confirmation."""
        try:
            from VOICE.voice_engine import voice_engine
            from FUNCTION.JARVIS_LISTEN.listen import listen_and_recognize
            voice_engine.speak(f"Are you sure you want to execute {tool_name}? Say yes to proceed or cancel to abort.")
            spoken = listen_and_recognize()
            if spoken:
                s = spoken.lower().strip()
                if any(w in s for w in ["yes", "proceed", "do it", "sure", "haan", "sahi hai"]):
                    return True
            return False
        except Exception:
            return False

    def request_confirmation(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None, is_voice: bool = False) -> bool:
        """Unified confirmation dispatcher."""
        if not self.requires_confirmation(tool_name):
            return True
        if is_voice:
            return self.request_confirmation_voice(tool_name)
        return self.request_confirmation_cli(tool_name, arguments)


# Global singleton instance
confirmation_center = ConfirmationCenter()
