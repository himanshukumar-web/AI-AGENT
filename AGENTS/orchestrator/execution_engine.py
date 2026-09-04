"""
JARVIS AI — Multi-Agent Execution Engine
Executes TaskGraph DAGs with parallel wave concurrency, dependencies, verification, and retries.
"""

import time
import concurrent.futures
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult, AgentStatus
from AGENTS.core.agent_registry import agent_registry
from AGENTS.orchestrator.task_graph import TaskGraph, TaskNode, NodeStatus
from AGENTS.orchestrator.delegation import agent_delegator
from AGENTS.policies.budgets import BudgetTracker, AgentBudget
from AGENTS.policies.permissions import permission_gate, AgentRiskLevel
from BRAIN.UTILS.logger import jarvis_logger


@dataclass
class ExecutionTimelineEvent:
    timestamp: str
    node_id: str
    agent: str
    event: str
    details: str = ""


@dataclass
class ExecutionResult:
    success: bool
    title: str
    completed_nodes: int
    total_nodes: int
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    interrupted: bool = False
    error: Optional[str] = None


class ExecutionEngine:
    """Executes multi-agent task graphs with concurrency, budgets, and verification."""

    def __init__(self, max_parallel_workers: int = 4):
        self.max_parallel_workers = max_parallel_workers

    def execute_graph(
        self,
        graph: TaskGraph,
        user_request: str,
        task_id: str,
        budget_tracker: Optional[BudgetTracker] = None,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> ExecutionResult:
        """Execute task graph respecting dependencies, parallelism, and budgets."""
        if budget_tracker is None:
            budget_tracker = BudgetTracker(AgentBudget())

        timeline: List[Dict[str, Any]] = []
        shared_memory: Dict[str, Any] = {}

        def log_event(node_id: str, agent: str, event: str, details: str = ""):
            t_str = time.strftime("%H:%M:%S")
            entry = {"time": t_str, "node_id": node_id, "agent": agent, "event": event, "details": details}
            timeline.append(entry)
            jarvis_logger.info("EXEC_ENGINE", f"[{t_str}] [{agent}] {event}: {details}")
            if event_callback:
                event_callback(f"[{agent}] {event}: {details}")

        log_event("root", "orchestrator", "TASK_STARTED", graph.title)

        waves = graph.get_execution_waves()

        for wave_idx, wave in enumerate(waves):
            # Check interruption & runtime budget before wave
            can_step, reason = budget_tracker.can_execute_step()
            if not can_step:
                log_event("root", "budget", "BUDGET_EXCEEDED", reason)
                return ExecutionResult(
                    success=False,
                    title=graph.title,
                    completed_nodes=len(graph.get_completed_node_ids()),
                    total_nodes=len(graph.nodes),
                    timeline=timeline,
                    outputs=shared_memory,
                    error=reason,
                )

            # Parallel dispatch if multiple independent nodes in wave
            if len(wave) > 1:
                log_event("wave", "engine", "PARALLEL_WAVE", f"Dispatching {len(wave)} nodes concurrently.")
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_parallel_workers, len(wave))) as executor:
                    futures = {
                        executor.submit(self._execute_single_node, node, graph, user_request, task_id, budget_tracker, shared_memory, log_event): node
                        for node in wave
                    }
                    for future in concurrent.futures.as_completed(futures):
                        node = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            node.status = NodeStatus.FAILED
                            log_event(node.id, node.agent_name, "NODE_EXCEPTION", str(e))
            else:
                # Single node execution
                self._execute_single_node(wave[0], graph, user_request, task_id, budget_tracker, shared_memory, log_event)

            # Check if critical failure halts workflow
            if graph.has_failures():
                log_event("root", "engine", "WORKFLOW_HALTED", "Critical task node failed.")
                break

        completed_count = len(graph.get_completed_node_ids())
        is_success = completed_count == len(graph.nodes) and not graph.has_failures()

        status_str = "COMPLETED" if is_success else "FAILED"
        log_event("root", "orchestrator", f"TASK_{status_str}", f"Processed {completed_count}/{len(graph.nodes)} steps.")

        return ExecutionResult(
            success=is_success,
            title=graph.title,
            completed_nodes=completed_count,
            total_nodes=len(graph.nodes),
            timeline=timeline,
            outputs=shared_memory,
            interrupted=False,
            error=None if is_success else "One or more critical tasks failed.",
        )

    def _execute_single_node(
        self,
        node: TaskNode,
        graph: TaskGraph,
        user_request: str,
        task_id: str,
        budget_tracker: BudgetTracker,
        shared_memory: Dict[str, Any],
        log_event: Callable,
    ):
        """Execute a single task node with retry and verification."""
        node.status = NodeStatus.RUNNING
        log_event(node.id, node.agent_name, "NODE_STARTED", node.description or node.action)

        agent = agent_delegator.resolve_agent(task_action=node.action, agent_hint=node.agent_name, prompt=user_request)
        if not agent:
            node.status = NodeStatus.FAILED
            log_event(node.id, node.agent_name, "AGENT_NOT_FOUND", f"No agent for action '{node.action}'")
            return

        # Prepare execution context with inputs + upstream shared memory
        node_inputs = dict(node.inputs)
        if "action" not in node_inputs:
            node_inputs["action"] = node.action
        context = AgentContext(
            task_id=task_id,
            step_id=node.id,
            user_request=user_request,
            inputs=node_inputs,
            shared_memory=shared_memory,
            budget_tracker=budget_tracker,
        )

        success = False
        attempt = 0
        last_error = ""
        result = None

        while attempt <= node.max_retries and not success:
            if context.is_cancelled():
                node.status = NodeStatus.CANCELLED
                log_event(node.id, agent.name, "NODE_CANCELLED", "User interrupted execution.")
                return

            if attempt > 0:
                can_retry, r_reason = budget_tracker.can_retry()
                if not can_retry:
                    break
                budget_tracker.record_retry()
                backoff = 0.2 * (2 ** (attempt - 1))
                time.sleep(backoff)
                log_event(node.id, agent.name, "RETRY_ATTEMPT", f"Attempt {attempt+1}/{node.max_retries+1}")

            try:
                result = agent.execute(context)
                if result.success:
                    # Mandatory Verification Step
                    if result.verification_required:
                        log_event(node.id, "verification", "VERIFICATION_STARTED", f"Verifying outcome for {node.id}")
                        ver_agent = agent_registry.get_agent("verification")
                        if ver_agent:
                            v_ctx = AgentContext(
                                task_id=task_id,
                                step_id=f"v_{node.id}",
                                user_request=user_request,
                                inputs={
                                    "agent_name": agent.name,
                                    "action": node.action,
                                    "criteria": result.verification_criteria or {},
                                    "output": result.output,
                                },
                                budget_tracker=budget_tracker,
                            )
                            v_res = ver_agent.execute(v_ctx)
                            if not v_res.success:
                                log_event(node.id, "verification", "VERIFICATION_FAILED", str(v_res.errors))
                                attempt += 1
                                last_error = f"Verification failed: {v_res.errors}"
                                continue
                            log_event(node.id, "verification", "VERIFICATION_PASSED", str(v_res.output))

                    success = True
                    break
                else:
                    last_error = ", ".join(result.errors) if result.errors else "Action failed."
            except Exception as e:
                last_error = str(e)

            attempt += 1

        node.result = result
        if success and result:
            node.status = NodeStatus.COMPLETED
            # Save node outputs into shared memory for downstream consumers
            shared_memory[node.id] = result.output
            if isinstance(result.output, dict):
                shared_memory.update(result.output)
            log_event(node.id, agent.name, "NODE_COMPLETED", f"Success on attempt {attempt+1}")
        else:
            node.status = NodeStatus.FAILED
            log_event(node.id, agent.name, "NODE_FAILED", last_error or "Execution failed.")


execution_engine = ExecutionEngine()
