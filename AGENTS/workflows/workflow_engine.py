"""
JARVIS AI — Autonomous Workflow Engine
Orchestrates end-to-end multi-agent workflows without manual intervention,
integrating with the scheduler, persistent state, verification pipeline, and notification channels.
"""

import uuid
from typing import Any, Callable, Dict, List, Optional
from AGENTS.orchestrator.task_graph import TaskGraph, TaskNode
from AGENTS.orchestrator.execution_engine import execution_engine, ExecutionResult
from AGENTS.orchestrator.state_store import task_state_store
from AGENTS.core.agent_registry import agent_registry
from AGENTS.policies.budgets import AgentBudget, BudgetTracker
from BRAIN.MEMORY.memory_manager import memory_manager
from BRAIN.UTILS.logger import jarvis_logger


class AutonomousWorkflowEngine:
    """Manages autonomous multi-agent task execution and background scheduled workflows."""

    def __init__(self):
        self._workflows: Dict[str, Dict[str, Any]] = {}

    def register_workflow(
        self,
        name: str,
        template_request: str,
        description: str = "",
        schedule_time: Optional[str] = None,
    ):
        """Register a reusable autonomous workflow template."""
        self._workflows[name.lower()] = {
            "name": name,
            "template_request": template_request,
            "description": description,
            "schedule_time": schedule_time,
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List registered workflow templates."""
        return list(self._workflows.values())

    def run_autonomous_workflow(
        self,
        request: str,
        workflow_title: Optional[str] = None,
        budget: Optional[AgentBudget] = None,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> ExecutionResult:
        """
        Execute an autonomous multi-agent workflow:
        1. Decompose request into structured TaskGraph.
        2. Persist state snapshot to SQLite.
        3. Execute graph with parallel waves, tool delegation, and verification.
        4. Record outcome in long-term memory.
        5. Notify user channels.
        """
        task_id = f"wf_{uuid.uuid4().hex[:8]}"
        budget_tracker = BudgetTracker(budget or AgentBudget())

        jarvis_logger.info("WORKFLOW", f"Initiating autonomous workflow '{task_id}': {request}")

        # 1. Planning Phase (decompose into TaskGraph)
        planner = agent_registry.get_agent("planner")
        plan_data = {}
        if planner:
            from AGENTS.core.agent_context import AgentContext
            p_ctx = AgentContext(task_id=task_id, step_id="plan", user_request=request, inputs={"request": request}, budget_tracker=budget_tracker)
            p_res = planner.execute(p_ctx)
            if p_res.success and isinstance(p_res.output, dict):
                plan_data = p_res.output

        title = workflow_title or plan_data.get("title", "Autonomous Workflow")
        tasks_list = plan_data.get("tasks", [])

        # Construct TaskGraph
        graph = TaskGraph(title=title)
        if tasks_list:
            for t in tasks_list:
                graph.add_node(TaskNode(
                    id=t["id"],
                    agent_name=t.get("agent", "conversation"),
                    action=t.get("action", "execute"),
                    description=t.get("description", ""),
                    inputs=t.get("inputs", {}),
                    dependencies=t.get("dependencies", []),
                ))
        else:
            # Single general node fallback
            graph.add_node(TaskNode(
                id="task_1",
                agent_name="conversation",
                action="chat",
                description="Process request",
                inputs={"prompt": request},
            ))

        # 2. Persist initial RUNNING state
        task_state_store.save_task_state(
            task_id=task_id,
            title=title,
            user_request=request,
            graph=graph,
            status="RUNNING",
        )

        # 3. Execution Phase
        result = execution_engine.execute_graph(
            graph=graph,
            user_request=request,
            task_id=task_id,
            budget_tracker=budget_tracker,
            event_callback=event_callback,
        )

        # 4. Update persistent state
        final_status = "COMPLETED" if result.success else "FAILED"
        task_state_store.save_task_state(
            task_id=task_id,
            title=title,
            user_request=request,
            graph=graph,
            status=final_status,
            shared_memory=result.outputs,
            errors=[result.error] if result.error else [],
        )

        # 5. Episodic Memory Recording
        try:
            tools_used = [e["details"] for e in result.timeline if e.get("event") == "NODE_COMPLETED"]
            summary_text = f"Workflow '{title}' finished with status {final_status}. Processed {result.completed_nodes}/{result.total_nodes} steps."
            memory_manager.record_episode(
                task_title=title,
                summary=summary_text,
                tools_used=tools_used,
            )
        except Exception:
            pass

        # 6. Notification Dispatch
        try:
            from BRAIN.NOTIFICATIONS.notification_manager import notification_manager
            notification_manager.notify_task_event(
                event_type="workflow_complete" if result.success else "workflow_failure",
                title=title,
                status=final_status,
                details=f"Completed {result.completed_nodes}/{result.total_nodes} steps.",
            )
        except Exception:
            pass

        return result


autonomous_workflow_engine = AutonomousWorkflowEngine()
