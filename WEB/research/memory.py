"""
JARVIS AI — Research Memory Layer
Persists curated research sessions, key findings, and sources in local SQLite database.
"""

from datetime import datetime
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
from config import RESEARCH_DB_PATH


class ResearchMemoryManager:
    """Manages long-term storage of user research sessions for follow-ups and auditing."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or RESEARCH_DB_PATH
        self._ensure_database()

    def _ensure_database(self):
        """Create research database and tables if missing."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS research_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE,
                        title TEXT,
                        query TEXT,
                        mode TEXT,
                        summary TEXT,
                        findings_json TEXT,
                        sources_json TEXT,
                        full_report TEXT,
                        created_at TEXT
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON research_sessions(query);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON research_sessions(created_at);")
                conn.commit()
        except Exception:
            pass

    def save_session(
        self,
        session_id: str,
        title: str,
        query: str,
        mode: str,
        summary: str,
        key_findings: List[str],
        sources: List[Dict[str, Any]],
        full_report: str,
    ) -> bool:
        """Store completed research session into database."""
        try:
            created_at = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO research_sessions
                    (session_id, title, query, mode, summary, findings_json, sources_json, full_report, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    title,
                    query,
                    mode,
                    summary,
                    json.dumps(key_findings),
                    json.dumps(sources),
                    full_report,
                    created_at,
                ))
                conn.commit()
                return True
        except Exception:
            return False

    def get_last_session(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recently completed research session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM research_sessions ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    data["findings"] = json.loads(data.get("findings_json") or "[]")
                    data["sources"] = json.loads(data.get("sources_json") or "[]")
                    return data
        except Exception:
            pass
        return None

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent research sessions."""
        sessions = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT id, session_id, title, query, mode, summary, created_at FROM research_sessions ORDER BY id DESC LIMIT ?", (limit,))
                for row in cursor.fetchall():
                    sessions.append(dict(row))
        except Exception:
            pass
        return sessions

    def search_saved_research(self, keyword: str) -> List[Dict[str, Any]]:
        """Find past research by topic or keyword."""
        results = []
        if not keyword:
            return results
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                pattern = f"%{keyword.strip().lower()}%"
                cursor.execute("""
                    SELECT * FROM research_sessions
                    WHERE LOWER(title) LIKE ? OR LOWER(query) LIKE ? OR LOWER(summary) LIKE ?
                    ORDER BY id DESC LIMIT 5
                """, (pattern, pattern, pattern))
                for row in cursor.fetchall():
                    d = dict(row)
                    d["findings"] = json.loads(d.get("findings_json") or "[]")
                    d["sources"] = json.loads(d.get("sources_json") or "[]")
                    results.append(d)
        except Exception:
            pass
        return results


# Global singleton instance
research_memory = ResearchMemoryManager()
