"""
JARVIS AI — Central Agent Orchestrator
Master coordinator executing the multi-agent pipeline:
Understand -> Plan DAG -> Delegate -> Execute -> Verify -> Remember -> Respond.
"""

import uuid
from typing import Any, Callable, Dict, List, Optional
from config import AGENT_SYSTEM_ENABLED
from AGENTS.orchestrator.task_graph import TaskGraph, TaskNode
from AGENTS.orchestrator.execution_engine import execution_engine, ExecutionResult
from AGENTS.orchestrator.state_store import task_state_store
from AGENTS.core.agent_registry import agent_registry
import AGENTS.agents
from AGENTS.policies.budgets import AgentBudget, BudgetTracker
from BRAIN.MEMORY.memory_manager import memory_manager
from BRAIN.UTILS.logger import jarvis_logger


class AgentOrchestrator:
    """Central multi-agent coordinator for complex and autonomous tasks."""

    def __init__(self):
        self.enabled = AGENT_SYSTEM_ENABLED

    def handle_request(
        self,
        user_request: str,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Main multi-agent orchestrator entry point:
        1. Decomposes request into DAG using PlannerAgent.
        2. Persists initial task state to SQLite.
        3. Executes graph across specialized agents with concurrency & verification.
        4. Saves state and records episodic memory.
        5. Formulates conversational, synthesized summary.
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        budget_tracker = BudgetTracker(AgentBudget())

        jarvis_logger.info("ORCHESTRATOR", f"Processing multi-agent request [{task_id}]: {user_request}")

        # 1. Plan Decomposition
        planner = agent_registry.get_agent("planner")
        plan_data = {}
        if planner:
            from AGENTS.core.agent_context import AgentContext
            p_ctx = AgentContext(
                task_id=task_id,
                step_id="plan",
                user_request=user_request,
                inputs={"request": user_request},
                budget_tracker=budget_tracker,
            )
            p_res = planner.execute(p_ctx)
            if p_res.success and isinstance(p_res.output, dict):
                plan_data = p_res.output

        title = plan_data.get("title", "Multi-Agent Request")
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
            graph.add_node(TaskNode(
                id="step_1",
                agent_name="conversation",
                action="chat",
                description="Respond to user",
                inputs={"prompt": user_request},
            ))

        # 2. Persist Initial State
        task_state_store.save_task_state(
            task_id=task_id,
            title=title,
            user_request=user_request,
            graph=graph,
            status="RUNNING",
        )

        # 3. Execution Phase
        exec_result = execution_engine.execute_graph(
            graph=graph,
            user_request=user_request,
            task_id=task_id,
            budget_tracker=budget_tracker,
            event_callback=event_callback,
        )

        # 4. Final State Persistence
        final_status = "COMPLETED" if exec_result.success else "FAILED"
        task_state_store.save_task_state(
            task_id=task_id,
            title=title,
            user_request=user_request,
            graph=graph,
            status=final_status,
            shared_memory=exec_result.outputs,
            errors=[exec_result.error] if exec_result.error else [],
            current_step=exec_result.completed_nodes,
        )

        # 5. Episodic Memory Recording
        try:
            tools_used = [e["details"] for e in exec_result.timeline if e.get("event") == "NODE_COMPLETED"]
            memory_manager.record_episode(
                task_title=title,
                summary=f"Processed {exec_result.completed_nodes}/{exec_result.total_nodes} subtasks. Status: {final_status}.",
                tools_used=tools_used,
            )
        except Exception:
            pass

        # 6. Response Synthesis
        if exec_result.interrupted:
            return "The task was interrupted and safely stopped."

        if not exec_result.success:
            return f"I encountered an issue executing '{title}'. {exec_result.error or 'One or more tasks failed verification.'}"

        # If research was part of outputs, summarize findings
        research_out = exec_result.outputs.get("task_1") or exec_result.outputs.get("research")
        if isinstance(research_out, dict) and "summary" in research_out:
            summary = research_out["summary"]
            return f"I've completed '{title}'. {summary}\nAll actions were independently verified."

        return f"I've successfully completed '{title}' ({exec_result.completed_nodes}/{exec_result.total_nodes} steps verified)."


# Global singleton instance
agent_orchestrator = AgentOrchestrator()
