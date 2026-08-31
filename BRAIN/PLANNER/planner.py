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
from BRAIN.MEMORY.memory_manager import memory_manager
from BRAIN.LLM.provider_manager import provider_manager
from BRAIN.UTILS.logger import jarvis_logger


@dataclass
class PlanStep:
    """A single discrete step in a task plan."""
    tool: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class TaskPlan:
    """An executable multi-step plan."""
    title: str
    steps: List[PlanStep] = field(default_factory=list)
    raw_prompt: str = ""


class TaskPlanner:
    """Plans and orchestrates sequential multi-tool task executions."""

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
                resp = active_prov.generate(planning_prompt, temperature=0.2, max_tokens=512)
                text = resp.text.strip()
                if "```" in text:
                    # Clean markdown fenced blocks
                    lines = [l for l in text.split("\n") if not l.startswith("```")]
                    text = "\n".join(lines).strip()
                data = json.loads(text)
                steps = [PlanStep(tool=s["tool"], arguments=s.get("arguments", {}), description=s.get("description", "")) for s in data.get("steps", [])]
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
        Sequentially execute plan steps with state updates and interruption checks.
        """
        task_state_manager.set_state(TaskState.EXECUTING, task_name=plan.title)
        results = []
        tools_executed = []

        for i, step in enumerate(plan.steps):
            # Check for user interruption before starting step
            if task_state_manager.is_interrupted():
                jarvis_logger.warning("PLANNER", f"Plan execution interrupted at step {i+1}/{len(plan.steps)}.")
                return {
                    "success": False,
                    "interrupted": True,
                    "message": "Task was interrupted and safely stopped.",
                    "completed_steps": results,
                }

            if step_callback:
                step_callback(f"Step {i+1}/{len(plan.steps)}: {step.description or step.tool}")

            res = tool_registry.execute_tool(
                name=step.tool,
                arguments=step.arguments,
                user_request=plan.raw_prompt,
            )
            results.append({"step": i + 1, "tool": step.tool, "result": res})
            tools_executed.append(step.tool)

            if not res.get("success", False):
                jarvis_logger.warning("PLANNER", f"Step {i+1} failed: {res.get('error')}")

        # Record completed episode in Episodic Memory
        summary_text = f"Executed {len(results)} steps for task '{plan.title}'."
        memory_manager.record_episode(
            task_title=plan.title,
            summary=summary_text,
            tools_used=tools_executed,
        )

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
