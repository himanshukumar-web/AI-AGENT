"""
JARVIS AI — Structured Logger
Clean categorized logging for INFO, WARNING, ERROR, and DEBUG without exposing secrets.
"""

import datetime
import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)


class JarvisLogger:
    """Structured console and file logger."""

    LEVEL_COLORS = {
        "DEBUG": Fore.LIGHTBLACK_EX,
        "INFO": Fore.CYAN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "SUCCESS": Fore.GREEN,
    }

    def __init__(self, log_to_console: bool = True):
        self.log_to_console = log_to_console

    def _sanitize(self, message: str) -> str:
        """Remove any accidental API key or sensitive token strings."""
        if not message:
            return ""
        sanitized = message
        for key_env in ["OPENAI_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"]:
            val = os.environ.get(key_env, "")
            if val and len(val) > 6:
                sanitized = sanitized.replace(val, "[REDACTED_API_KEY]")
        return sanitized

    def log(self, level: str, category: str, message: str):
        """Format and output log record."""
        clean_msg = self._sanitize(message)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        color = self.LEVEL_COLORS.get(level.upper(), Fore.WHITE)

        if self.log_to_console:
            prefix = f"{color}[{level.upper()}]{Style.RESET_ALL}"
            cat_str = f"{Fore.LIGHTBLUE_EX}[{category}]{Style.RESET_ALL}"
            print(f"  {timestamp} {prefix} {cat_str} {clean_msg}")

    def info(self, category: str, message: str):
        self.log("INFO", category, message)

    def warning(self, category: str, message: str):
        self.log("WARNING", category, message)

    def error(self, category: str, message: str):
        self.log("ERROR", category, message)

    def debug(self, category: str, message: str):
        self.log("DEBUG", category, message)

    def success(self, category: str, message: str):
        self.log("SUCCESS", category, message)


# Global singleton instance
jarvis_logger = JarvisLogger()
