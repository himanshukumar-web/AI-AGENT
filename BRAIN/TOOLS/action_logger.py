"""
JARVIS AI — Action History & Tool Execution Logger
Maintains persistent audit logs of tool executions in SQLite without logging credentials.
"""

import datetime
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class ActionLogger:
    """Logs tool actions, execution duration, and results to SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from config import MEMORY_DB_PATH
            self.db_path = MEMORY_DB_PATH
        else:
            self.db_path = db_path

        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    parameters_json TEXT,
                    user_request TEXT,
                    result_json TEXT,
                    success INTEGER NOT NULL,
                    duration_ms REAL NOT NULL,
                    risk_level TEXT NOT NULL
                )
            """)
            conn.commit()

    def log_action(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: float,
        risk_level: str = "low",
        user_request: str = "",
    ):
        """Log a tool execution event."""
        now = datetime.datetime.now().isoformat()
        try:
            # Sanitize parameters
            params_sanitized = {k: v for k, v in parameters.items() if "key" not in k.lower() and "token" not in k.lower()}
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO action_history (timestamp, tool_name, parameters_json, user_request, result_json, success, duration_ms, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now,
                    tool_name,
                    json.dumps(params_sanitized, default=str),
                    user_request[:200] if user_request else "",
                    json.dumps(result, default=str)[:500],
                    1 if result.get("success", False) else 0,
                    round(duration_ms, 2),
                    risk_level.lower(),
                ))
                conn.commit()
        except Exception:
            pass

    def get_recent_actions(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieve recent tool action logs."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, tool_name, parameters_json, user_request, result_json, success, duration_ms, risk_level
                    FROM action_history
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []


# Global singleton instance
action_logger = ActionLogger()
