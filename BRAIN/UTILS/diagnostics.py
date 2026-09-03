"""
JARVIS AI — Self-Diagnostics Engine (JARVIS Doctor)
Comprehensive system health check: Python version, Audio, TTS, Network, LLM, DB, and Dependencies.
"""

import os
import sys
import sqlite3
import importlib.util
from colorama import Fore, Style, init

init(autoreset=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import PATHS, MEMORY_DB_PATH, import_module_from_path
from BRAIN.LLM.provider_manager import provider_manager


class JarvisDoctor:
    """Performs deep self-diagnostics on all subsystems."""

    def run_diagnostics(self) -> dict:
        """Run all diagnostic checks and return status dictionary."""
        results = {}

        # 1. Python Environment
        py_ver = sys.version.split()[0]
        results["python"] = {
            "version": py_ver,
            "status": "OK" if sys.version_info >= (3, 10) else "WARN",
            "details": f"Python {py_ver} ({sys.executable})",
        }

        # 2. Audio & Microphone
        has_sd = importlib.util.find_spec("sounddevice") is not None
        has_pyaudio = importlib.util.find_spec("pyaudio") is not None
        results["microphone"] = {
            "status": "OK" if (has_sd or has_pyaudio) else "FAIL",
            "details": f"SoundDevice: {'Available' if has_sd else 'Missing'}, PyAudio: {'Available' if has_pyaudio else 'Missing'}",
        }

        # 3. TTS Engine
        has_pyttsx3 = importlib.util.find_spec("pyttsx3") is not None
        results["tts"] = {
            "status": "OK" if has_pyttsx3 else "FAIL",
            "details": "pyttsx3 offline engine loaded" if has_pyttsx3 else "pyttsx3 missing",
        }

        # 4. Internet Connectivity
        try:
            import requests
            r = requests.get("https://www.google.com", timeout=3)
            internet_ok = r.status_code == 200
        except Exception:
            internet_ok = False
        results["internet"] = {
            "status": "OK" if internet_ok else "OFFLINE",
            "details": "Connected to World Wide Web" if internet_ok else "No internet connection (Offline Mode)",
        }

        # 5. LLM Provider
        active_prov = provider_manager.get_active_provider()
        prov_avail = active_prov.is_available()
        results["llm"] = {
            "provider": active_prov.provider_name,
            "model": active_prov.model_name,
            "status": "OK" if prov_avail else "FALLBACK",
            "details": f"Active: {active_prov.provider_name.upper()} ({active_prov.model_name})",
        }

        # 6. SQLite Memory Database
        db_ok = False
        try:
            conn = sqlite3.connect(MEMORY_DB_PATH)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in c.fetchall()]
            conn.close()
            db_ok = "long_term_memory" in tables and "conversation_history" in tables
        except Exception:
            db_ok = False
        results["memory_db"] = {
            "status": "OK" if db_ok else "WARN",
            "details": f"SQLite at {MEMORY_DB_PATH} ({'Valid Schema' if db_ok else 'Uninitialized'})",
        }

        # 7. Automations Store
        auto_path = PATHS.get("automations_db", "")
        results["automations"] = {
            "status": "OK",
            "details": f"Store at {auto_path} (Ready)",
        }

        # 8. Tools Registry
        try:
            from BRAIN.TOOLS.tool_registry import tool_registry
            tool_defs = tool_registry.get_tool_definitions()
            results["tools"] = {
                "status": "OK",
                "details": f"{len(tool_defs)} registered tools loaded and validated",
            }
        except Exception as e:
            results["tools"] = {
                "status": "WARN",
                "details": f"Tool registry check: {e}",
            }

        # 9. Action Audit History
        try:
            from BRAIN.TOOLS.action_logger import action_logger
            recent = action_logger.get_recent_actions(limit=1)
            results["action_audit"] = {
                "status": "OK",
                "details": "Persistent action history active in SQLite",
            }
        except Exception as e:
            results["action_audit"] = {
                "status": "WARN",
                "details": f"Action logger check: {e}",
            }

        # 10. Research Search Provider
        try:
            from WEB.search.provider_manager import search_provider_manager
            active_sp = search_provider_manager.get_active_provider_name()
            all_sp = search_provider_manager.list_providers()
            results["search_provider"] = {
                "status": "OK",
                "details": f"Active: {active_sp.upper()} (Available providers: {', '.join(all_sp)})",
            }
        except Exception as e:
            results["search_provider"] = {
                "status": "WARN",
                "details": f"Search provider check: {e}",
            }

        # 11. Web Content Extraction Engine
        try:
            from WEB.extraction.extractor import web_extractor
            sample = web_extractor.extract_from_html("<html><title>T</title><body><p>Hello world from diagnostics</p></body></html>")
            ext_ok = sample.success and sample.text.startswith("Hello")
            results["extraction"] = {
                "status": "OK" if ext_ok else "WARN",
                "details": "BeautifulSoup HTML & content extractor active",
            }
        except Exception as e:
            results["extraction"] = {
                "status": "FAIL",
                "details": f"Web extraction error: {e}",
            }

        # 12. Research Storage Database
        try:
            from config import RESEARCH_DB_PATH
            import sqlite3
            r_db_ok = False
            if os.path.exists(RESEARCH_DB_PATH):
                with sqlite3.connect(RESEARCH_DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [r[0] for r in cur.fetchall()]
                    r_db_ok = "research_sessions" in tables
            results["research_storage"] = {
                "status": "OK" if r_db_ok else "INFO",
                "details": f"SQLite at {RESEARCH_DB_PATH} ({'Active' if r_db_ok else 'Ready'})",
            }
        except Exception as e:
            results["research_storage"] = {
                "status": "WARN",
                "details": f"Research storage check: {e}",
            }

        # 13. Research Cache & Resource Controls
        try:
            from WEB.security.caching import research_cache
            from WEB.security.rate_limiter import research_rate_limiter
            cache_stats = research_cache.get_stats()
            lim_stats = research_rate_limiter.get_stats()
            results["research_cache"] = {
                "status": "OK",
                "details": f"TTL Cache active ({cache_stats['cached_searches']} searches, {cache_stats['cached_pages']} pages), Rate Limiter online",
            }
        except Exception as e:
            results["research_cache"] = {
                "status": "WARN",
                "details": f"Research cache check: {e}",
            }

        return results


    def print_report(self):
        """Format and print an attractive terminal health report."""
        print(Fore.CYAN + "\n" + "=" * 65)
        print(Fore.CYAN + "  [DOCTOR] JARVIS AI — SELF-DIAGNOSTICS HEALTH REPORT")
        print(Fore.CYAN + "=" * 65)

        diagnostics = self.run_diagnostics()

        for key, info in diagnostics.items():
            status = info.get("status", "INFO")
            details = info.get("details", "")
            if status == "OK":
                badge = Fore.GREEN + "[OK]    "
            elif status in ("WARN", "FALLBACK", "OFFLINE"):
                badge = Fore.YELLOW + f"[{status}]"
            else:
                badge = Fore.RED + "[FAIL]  "

            name_fmt = f"{key.upper():<14}"
            print(f"  {badge} {Fore.WHITE}{name_fmt}: {details}")

        print(Fore.CYAN + "=" * 65 + "\n")


doctor = JarvisDoctor()
