"""
JARVIS AI — Lightweight Task Planner & Multi-Step Executor
Decomposes complex user requests into ordered, validated tool steps.
Enforces safety: Only registered tools are executed; arbitrary scripts are forbidden.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from colorama import Fore

from BRAIN.TOOLS.tool_registry import tool_registry
from BRAIN.CORE_AGENT.task_state import task_state_manager, TaskState
from BRAIN.CORE_AGENT.task_manager import task_manager
from BRAIN.MEMORY.memory_manager import memory_manager
from BRAIN.LLM.provider_manager import provider_manager
from BRAIN.UTILS.logger import jarvis_logger


@dataclass
class PlanStep:
    """A single discrete step in a task plan."""
    tool: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    retry_count: int = 1


@dataclass
class TaskPlan:
    """An executable multi-step plan."""
    title: str
    steps: List[PlanStep] = field(default_factory=list)
    raw_prompt: str = ""

    def get_visibility_summary(self) -> str:
        """Return a concise, high-level explanation of planned steps."""
        if not self.steps:
            return "No steps planned."
        step_lines = [f"{i+1}. {s.description or s.tool}" for i, s in enumerate(self.steps)]
        return f"Sure, I'll:\n" + "\n".join(step_lines)


class TaskPlanner:
    """Plans and orchestrates sequential multi-tool task executions with failure recovery."""

    def __init__(self):
        pass

    def create_plan(self, prompt: str) -> TaskPlan:
        """
        Analyze complex instruction and generate structured PlanSteps.
        """
        task_state_manager.set_state(TaskState.PLANNING, task_name=prompt[:40])
        jarvis_logger.info("PLANNER", f"Creating execution plan for: '{prompt}'")

        tools_schema = tool_registry.get_tool_definitions()
        tools_summary = "\n".join([f"- {t['name']}: {t['description']}" for t in tools_schema])

        planning_prompt = f"""You are the Task Planner for JARVIS AI.
Decompose the following user request into a minimal sequence of discrete tool steps.

AVAILABLE TOOLS:
{tools_summary}

RULES:
1. ONLY use the registered tool names listed above.
2. Return ONLY a valid JSON object in the format:
{{
  "title": "Short title of the task",
  "steps": [
    {{
      "tool": "canonical.tool.name",
      "arguments": {{"param": "value"}},
      "description": "Brief description of this step"
    }}
  ]
}}
3. Do NOT include markdown code blocks or additional conversational text outside the JSON.

USER REQUEST: {prompt}
"""
        try:
            active_prov = provider_manager.get_active_provider()
            if active_prov.provider_name != "offline_fallback":
                resp = active_prov.generate(planning_prompt, temperature=0.2, max_tokens=256)
                text = resp.text.strip()
                if "```" in text:
                    # Clean markdown fenced blocks
                    lines = [l for l in text.split("\n") if not l.startswith("```")]
                    text = "\n".join(lines).strip()
                data = json.loads(text)
                steps = [PlanStep(tool=s["tool"], arguments=s.get("arguments", {}), description=s.get("description", "")) for s in data.get("steps", [])]
                if steps:
                    return TaskPlan(title=data.get("title", "Multi-Step Task"), steps=steps, raw_prompt=prompt)
        except Exception as e:
            jarvis_logger.warning("PLANNER", f"LLM planning failed ({e}), using heuristic planner.")

        # Fallback Heuristic Planner for common multi-step patterns
        steps = []
        p_lower = prompt.lower()
        if "python" in p_lower and ("course" in p_lower or "tutorial" in p_lower):
            steps.append(PlanStep(tool="research.deep_search", arguments={"query": "best python courses tutorials"}, description="Search Python tutorials"))
            steps.append(PlanStep(tool="memory.remember", arguments={"key": "recommended_python_resources", "value": "Python Official Docs, Coursera, freeCodeCamp", "category": "fact"}, description="Save results in memory"))

        elif "youtube" in p_lower and "search" in p_lower:
            query = prompt.replace("search youtube for", "").replace("search on youtube", "").strip()
            steps.append(PlanStep(tool="youtube.search", arguments={"query": query}, description=f"Search YouTube for {query}"))

        else:
            steps.append(PlanStep(tool="browser.search", arguments={"query": prompt}, description=f"Search Google for {prompt}"))

        return TaskPlan(title="Multi-Step Task", steps=steps, raw_prompt=prompt)

    def execute_plan(
        self,
        plan: TaskPlan,
        step_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Sequentially execute plan steps with state updates, retries, and interruption checks.
        """
        task_state_manager.set_state(TaskState.EXECUTING, task_name=plan.title)
        active_rec = task_manager.create_task(name=plan.title, total_steps=len(plan.steps))
        results = []
        tools_executed = []

        for i, step in enumerate(plan.steps):
            # Check for user interruption before starting step
            if task_state_manager.is_interrupted():
                jarvis_logger.warning("PLANNER", f"Plan execution interrupted at step {i+1}/{len(plan.steps)}.")
                task_manager.cancel_current_task()
                return {
                    "success": False,
                    "interrupted": True,
                    "message": "Task was interrupted and safely stopped.",
                    "completed_steps": results,
                }

            desc = step.description or step.tool
            task_manager.update_step(step_idx=i + 1, description=desc)

            if step_callback:
                step_callback(f"Step {i+1}/{len(plan.steps)}: {desc}")

            # Step execution with transient retry logic
            success = False
            res = {}
            for attempt in range(max(1, step.retry_count + 1)):
                res = tool_registry.execute_tool(
                    name=step.tool,
                    arguments=step.arguments,
                    user_request=plan.raw_prompt,
                )
                if res.get("success", False):
                    success = True
                    break
                jarvis_logger.warning("PLANNER", f"Step {i+1} attempt {attempt+1} failed: {res.get('error')}")

            results.append({"step": i + 1, "tool": step.tool, "result": res, "success": success})
            tools_executed.append(step.tool)

            if not success:
                jarvis_logger.warning("PLANNER", f"Step {i+1} permanently failed. Determining recovery path.")
                # Non-critical failure in search/memory allows graceful continuation; critical failure halts safely
                if i == 0 and len(plan.steps) == 1:
                    task_manager.fail_task(res.get("error", "Execution failed"))
                    return {"success": False, "interrupted": False, "error": res.get("error"), "results": results}

        # Record completed episode in Episodic Memory
        summary_text = f"Executed {len(results)} steps for task '{plan.title}'."
        memory_manager.record_episode(
            task_title=plan.title,
            summary=summary_text,
            tools_used=tools_executed,
        )

        task_manager.complete_task(result=results)
        task_state_manager.set_state(TaskState.COMPLETED)
        return {
            "success": True,
            "interrupted": False,
            "title": plan.title,
            "results": results,
            "summary": summary_text,
        }


# Global singleton instance
task_planner = TaskPlanner()

