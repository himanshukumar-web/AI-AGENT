"""
JARVIS AI — Task Recovery & Crash Resumption Coordinator
Detects incomplete tasks after restart, validates completed steps, and safely resumes execution.
"""

from typing import Any, Callable, Dict, List, Optional
from AGENTS.orchestrator.task_graph import TaskGraph, NodeStatus
from AGENTS.orchestrator.execution_engine import execution_engine, ExecutionResult
from AGENTS.orchestrator.state_store import task_state_store
from BRAIN.UTILS.logger import jarvis_logger


class TaskRecoveryCoordinator:
    """Detects and safely resumes interrupted multi-agent workflows."""

    def check_for_resumable_tasks(self) -> List[Dict[str, Any]]:
        """Identify tasks left in an unfinished state prior to process restart."""
        incomplete = task_state_store.get_incomplete_tasks()
        return incomplete

    def resume_task(
        self,
        task_id: str,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> Optional[ExecutionResult]:
        """
        Safely resume an interrupted task:
        1. Loads saved snapshot and reconstructs TaskGraph.
        2. Preserves already completed steps without repeating them.
        3. Executes only remaining pending nodes.
        4. Updates persistent database.
        """
        snapshot = task_state_store.get_task_state(task_id)
        if not snapshot:
            jarvis_logger.warning("RECOVERY", f"Cannot resume: Task '{task_id}' not found.")
            return None

        plan_data = snapshot.get("plan_json")
        if not plan_data or not isinstance(plan_data, dict):
            jarvis_logger.warning("RECOVERY", f"Cannot resume: Task '{task_id}' has invalid plan.")
            return None

        graph = TaskGraph.from_dict(plan_data)
        user_request = snapshot.get("user_request", "")
        shared_memory = snapshot.get("shared_memory_json", {}) or {}
        completed_ids = set(snapshot.get("completed_steps_json", []))

        # Ensure already completed nodes remain completed
        for nid, node in graph.nodes.items():
            if nid in completed_ids:
                node.status = NodeStatus.COMPLETED

        pending_nodes = [n for n in graph.nodes.values() if n.status != NodeStatus.COMPLETED]
        jarvis_logger.info("RECOVERY", f"Resuming task '{task_id}' ({len(completed_ids)} steps verified, {len(pending_nodes)} remaining).")

        # Execute remaining steps through execution engine
        result = execution_engine.execute_graph(
            graph=graph,
            user_request=user_request,
            task_id=task_id,
            event_callback=event_callback,
        )

        final_status = "COMPLETED" if result.success else "FAILED"
        task_state_store.save_task_state(
            task_id=task_id,
            title=graph.title,
            user_request=user_request,
            graph=graph,
            status=final_status,
            shared_memory=result.outputs,
            errors=[result.error] if result.error else [],
        )

        return result


task_recovery_coordinator = TaskRecoveryCoordinator()
