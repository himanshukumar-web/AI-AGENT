"""
JARVIS AI — Advanced Task Manager (Phase 4)
Manages the complete lifecycle, progress tracking, and visibility of multi-step agent tasks.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskRecord:
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    created_time: float = field(default_factory=time.time)
    updated_time: float = field(default_factory=time.time)
    current_step: int = 0
    total_steps: int = 1
    current_step_description: str = ""
    progress_percent: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_time": self.created_time,
            "updated_time": self.updated_time,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_description": self.current_step_description,
            "progress_percent": self.progress_percent,
            "result": self.result,
            "error": self.error,
        }


class TaskManager:
    """Central singleton managing active and historical tasks."""

    def __init__(self):
        self._active_task: Optional[TaskRecord] = None
        self._task_history: List[TaskRecord] = []

    def create_task(self, name: str, total_steps: int = 1) -> TaskRecord:
        """Initialize a new task."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = TaskRecord(id=task_id, name=name, total_steps=max(1, total_steps), status=TaskStatus.RUNNING)
        self._active_task = task
        self._task_history.append(task)
        return task

    def get_current_task(self) -> Optional[TaskRecord]:
        """Return the currently executing task if any."""
        if self._active_task and self._active_task.status in [TaskStatus.RUNNING, TaskStatus.WAITING_CONFIRMATION]:
            return self._active_task
        return None

    def update_step(self, step_idx: int, description: str = "") -> Optional[TaskRecord]:
        """Update step progress on the active task."""
        if not self._active_task:
            return None
        self._active_task.current_step = step_idx
        self._active_task.current_step_description = description
        if self._active_task.total_steps > 0:
            self._active_task.progress_percent = min(100, int((step_idx / self._active_task.total_steps) * 100))
        self._active_task.updated_time = time.time()
        return self._active_task

    def complete_task(self, result: Optional[Any] = None) -> Optional[TaskRecord]:
        """Mark active task as successfully completed."""
        if not self._active_task:
            return None
        self._active_task.status = TaskStatus.COMPLETED
        self._active_task.progress_percent = 100
        self._active_task.result = result
        self._active_task.updated_time = time.time()
        completed = self._active_task
        self._active_task = None
        return completed

    def fail_task(self, error: str) -> Optional[TaskRecord]:
        """Mark active task as failed."""
        if not self._active_task:
            return None
        self._active_task.status = TaskStatus.FAILED
        self._active_task.error = error
        self._active_task.updated_time = time.time()
        failed = self._active_task
        self._active_task = None
        return failed

    def cancel_current_task(self) -> Optional[TaskRecord]:
        """Cancel the active task."""
        if not self._active_task:
            return None
        self._active_task.status = TaskStatus.CANCELLED
        self._active_task.updated_time = time.time()
        cancelled = self._active_task
        self._active_task = None
        return cancelled

    def get_status_summary(self) -> str:
        """Return a concise, natural summary of active task progress."""
        task = self.get_current_task()
        if not task:
            return "No active background tasks are currently running."
        return f"Currently working on '{task.name}' (Step {task.current_step}/{task.total_steps}: {task.current_step_description}, {task.progress_percent}% complete)."


# Global singleton instance
task_manager = TaskManager()
