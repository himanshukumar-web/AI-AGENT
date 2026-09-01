"""
JARVIS AI — Memory 2.0 (Short-Term, Long-Term, and Episodic Architecture)
SQLite storage for:
1. Long-Term Facts & Preferences (key-value + category)
2. Episodic Task Memory (completed plans, summaries, and key outcomes)
3. Session Conversation Turns
Provides relevance-based context retrieval so full DB is never sent to the LLM.
"""

import datetime
import os
import sqlite3
from typing import Any, Dict, List, Optional


class MemoryManager:
    """Memory 2.0 Engine managing Long-Term, Episodic, and Conversation History."""

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
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Long-Term Memory (User Preferences & Facts)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_name TEXT UNIQUE NOT NULL,
                    value_text TEXT NOT NULL,
                    category TEXT DEFAULT 'preference',
                    importance INTEGER DEFAULT 3,
                    source TEXT DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # 2. Episodic Memory (Completed complex tasks & automations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    tools_used_json TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            # 3. Conversation Turn History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls_json TEXT,
                    importance INTEGER DEFAULT 1,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    SENSITIVE_KEYWORDS = ["api_key", "apikey", "password", "secret", "token", "auth_token", "private_key", "bearer "]

    # ── Long-Term Memory ────────────────────────────────────────────────────
    def store_fact(self, key: str, value: str, category: str = "preference", importance: int = 3, source: str = "user") -> bool:
        """Store or update a user preference or fact with sensitive information protection."""
        if not key or not value:
            return False

        clean_key = key.strip().lower()
        val_str = value.strip()

        # Reject storage of raw passwords, API keys, and sensitive tokens
        if any(sk in clean_key for sk in self.SENSITIVE_KEYWORDS) or any(sk in val_str.lower() for sk in self.SENSITIVE_KEYWORDS):
            return False

        now = datetime.datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO long_term_memory (key_name, value_text, category, importance, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(key_name) DO UPDATE SET
                        value_text=excluded.value_text,
                        category=excluded.category,
                        importance=excluded.importance,
                        source=excluded.source,
                        updated_at=excluded.updated_at
                """, (clean_key, val_str, category.lower(), importance, source, now, now))
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
        """Search stored facts by query or category."""
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
        """Delete a specific stored fact."""
        clean_key = key.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memory WHERE key_name = ?", (clean_key,))
            conn.commit()
            return cursor.rowcount > 0

    def forget_facts_matching(self, query: str) -> int:
        """Forget facts matching keyword or topic."""
        clean_query = query.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memory WHERE key_name LIKE ? OR value_text LIKE ?", (f"%{clean_query}%", f"%{clean_query}%"))
            conn.commit()
            return cursor.rowcount

    # ── Episodic Memory ─────────────────────────────────────────────────────
    def record_episode(self, task_title: str, summary: str, tools_used: Optional[List[str]] = None) -> bool:
        """Record a completed complex multi-step task."""
        now = datetime.datetime.now().isoformat()
        import json
        tools_json = json.dumps(tools_used or [])
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO episodic_memory (task_title, summary, tools_used_json, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (task_title, summary, tools_json, now))
                conn.commit()
                return True
        except Exception:
            return False

    def get_recent_episodes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent episodic summaries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, task_title, summary, timestamp FROM episodic_memory ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    # ── Relevance-Based Retrieval ───────────────────────────────────────────
    def search_relevant_context(self, user_prompt: str, max_items: int = 4) -> str:
        """
        Extract only contextually relevant facts for the current query
        to avoid sending the entire database to the LLM.
        """
        words = [w.lower() for w in user_prompt.split() if len(w) > 3]
        if not words:
            # Return top preferences if no specific keywords match
            facts = self.recall_facts(category="preference")[:max_items]
        else:
            scored_facts = []
            all_facts = self.recall_facts()
            for f in all_facts:
                score = 0
                k = f["key"].lower()
                v = f["value"].lower()
                for w in words:
                    if w in k:
                        score += 2
                    if w in v:
                        score += 1
                if score > 0:
                    scored_facts.append((score, f))
            scored_facts.sort(key=lambda x: x[0], reverse=True)
            facts = [sf[1] for sf in scored_facts[:max_items]]
            if not facts:
                facts = self.recall_facts(category="preference")[:max_items]

        if not facts:
            return ""
        return "\n".join([f"- {f['key']}: {f['value']}" for f in facts])

    # ── Conversation Turn Logging ───────────────────────────────────────────
    def log_turn(self, session_id: str, role: str, content: str, tool_calls_json: Optional[str] = None):
        """Log a conversation turn."""
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

    def cleanup_old_history(self, days: int = 30) -> int:
        """
        Prune low-importance conversation turns older than given days.
        Preserves high-importance turns and all long-term preferences.
        """
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM conversation_history
                    WHERE timestamp < ? AND importance < 3
                """, (cutoff,))
                conn.commit()
                return cursor.rowcount
        except Exception:
            return 0

    def clear_all(self):
        """Reset all tables (testing utility)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memory")
            cursor.execute("DELETE FROM episodic_memory")
            cursor.execute("DELETE FROM conversation_history")
            conn.commit()


# Global singleton instance
memory_manager = MemoryManager()

