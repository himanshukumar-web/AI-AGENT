"""
JARVIS AI — Long-Term & Short-Term SQLite Memory Architecture
Persistent lightweight local database for user preferences, facts, and session logs.
Does NOT store sensitive passwords or system secrets.
"""

import datetime
import os
import sqlite3
from typing import Any, Dict, List, Optional


class MemoryManager:
    """Manages SQLite-based long-term facts and conversation persistence."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from config import MEMORY_DB_PATH
            self.db_path = MEMORY_DB_PATH
        else:
            self.db_path = db_path

        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Long-term memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_name TEXT UNIQUE NOT NULL,
                    value_text TEXT NOT NULL,
                    category TEXT DEFAULT 'preference',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # 2. Conversation turn history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls_json TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    # ── Long-Term Memory (Preferences & Facts) ──────────────────────────────
    def store_fact(self, key: str, value: str, category: str = "preference") -> bool:
        """Store or update a user preference or fact."""
        now = datetime.datetime.now().isoformat()
        clean_key = key.strip().lower()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO long_term_memory (key_name, value_text, category, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(key_name) DO UPDATE SET
                        value_text=excluded.value_text,
                        category=excluded.category,
                        updated_at=excluded.updated_at
                """, (clean_key, value.strip(), category.lower(), now, now))
                conn.commit()
                return True
        except Exception:
            return False

    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a specific fact by key."""
        clean_key = key.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value_text FROM long_term_memory WHERE key_name = ?", (clean_key,))
            row = cursor.fetchone()
            if row:
                return row["value_text"]
        return None

    def recall_facts(self, query: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search stored facts by keyword or category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if query and category:
                cursor.execute(
                    "SELECT key_name, value_text, category, updated_at FROM long_term_memory WHERE (key_name LIKE ? OR value_text LIKE ?) AND category = ?",
                    (f"%{query}%", f"%{query}%", category.lower())
                )
            elif query:
                cursor.execute(
                    "SELECT key_name, value_text, category, updated_at FROM long_term_memory WHERE key_name LIKE ? OR value_text LIKE ?",
                    (f"%{query}%", f"%{query}%")
                )
            elif category:
                cursor.execute(
                    "SELECT key_name, value_text, category, updated_at FROM long_term_memory WHERE category = ?",
                    (category.lower(),)
                )
            else:
                cursor.execute("SELECT key_name, value_text, category, updated_at FROM long_term_memory ORDER BY updated_at DESC LIMIT 20")

            rows = cursor.fetchall()
            return [{"key": r["key_name"], "value": r["value_text"], "category": r["category"], "updated_at": r["updated_at"]} for r in rows]

    def delete_fact(self, key: str) -> bool:
        """Delete a stored fact by key."""
        clean_key = key.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memory WHERE key_name = ?", (clean_key,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all(self):
        """Clear all stored data (testing/reset utility)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memory")
            cursor.execute("DELETE FROM conversation_history")
            conn.commit()

    # ── Conversation Turn Logging ───────────────────────────────────────────
    def log_turn(self, session_id: str, role: str, content: str, tool_calls_json: Optional[str] = None):
        """Log a conversation message."""
        now = datetime.datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_history (session_id, role, content, tool_calls_json, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, role, content, tool_calls_json, now))
                conn.commit()
        except Exception:
            pass

    def get_recent_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM conversation_history
                WHERE session_id = ?
                ORDER BY id DESC LIMIT ?
            """, (session_id, limit))
            rows = cursor.fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# Global singleton instance
memory_manager = MemoryManager()
