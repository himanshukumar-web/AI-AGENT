"""
JARVIS AI — Persistent Task State Store
Stores full multi-agent task lifecycles in SQLite (DATA/jarvis_tasks.db) for crash recovery and restart resume.
"""

import json
import sqlite3
import datetime
from typing import Any, Dict, List, Optional
from config import TASKS_DB_PATH
from AGENTS.orchestrator.task_graph import TaskGraph, NodeStatus


class TaskStateStore:
    """Persistent SQLite store for multi-agent tasks and DAG states."""

    def __init__(self, db_path: str = TASKS_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables and indexes if not existing."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS task_records (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_request TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    total_steps INTEGER DEFAULT 1,
                    completed_steps_json TEXT,
                    shared_memory_json TEXT,
                    errors_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON task_records(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_updated ON task_records(updated_at DESC)")
            conn.commit()

    def save_task_state(
        self,
        task_id: str,
        title: str,
        user_request: str,
        graph: TaskGraph,
        status: str,
        shared_memory: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        current_step: int = 0,
    ) -> bool:
        """Save or update task state snapshot."""
        now = datetime.datetime.now().isoformat()
        plan_json = json.dumps(graph.to_dict(), default=str)
        completed = list(graph.get_completed_node_ids())
        completed_json = json.dumps(completed)
        mem_json = json.dumps(shared_memory or {}, default=str)
        err_json = json.dumps(errors or [])

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO task_records (
                        task_id, title, user_request, plan_json, status, current_step,
                        total_steps, completed_steps_json, shared_memory_json, errors_json,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        status=excluded.status,
                        current_step=excluded.current_step,
                        plan_json=excluded.plan_json,
                        completed_steps_json=excluded.completed_steps_json,
                        shared_memory_json=excluded.shared_memory_json,
                        errors_json=excluded.errors_json,
                        updated_at=excluded.updated_at
                """, (
                    task_id, title, user_request, plan_json, status.upper(), current_step,
                    len(graph.nodes), completed_json, mem_json, err_json, now, now
                ))
                conn.commit()
                return True
        except Exception:
            return False

    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task snapshot by task ID."""
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM task_records WHERE task_id = ?", (task_id,))
                row = cur.fetchone()
                if row:
                    return self._row_to_dict(row)
        except Exception:
            pass
        return None

    def get_incomplete_tasks(self) -> List[Dict[str, Any]]:
        """Find tasks interrupted before reaching a terminal status."""
        active_statuses = ("RUNNING", "PLANNING", "WAITING_APPROVAL", "PAUSED", "VERIFYING")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                placeholders = ",".join("?" for _ in active_statuses)
                cur.execute(f"SELECT * FROM task_records WHERE status IN ({placeholders}) ORDER BY updated_at DESC", active_statuses)
                rows = cur.fetchall()
                return [self._row_to_dict(r) for r in rows]
        except Exception:
            return []

    def list_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent tasks across all statuses."""
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM task_records ORDER BY updated_at DESC LIMIT ?", (limit,))
                rows = cur.fetchall()
                return [self._row_to_dict(r) for r in rows]
        except Exception:
            return []

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        for json_col in ["plan_json", "completed_steps_json", "shared_memory_json", "errors_json"]:
            if d.get(json_col):
                try:
                    d[json_col] = json.loads(d[json_col])
                except Exception:
                    pass
        return d


task_state_store = TaskStateStore()
