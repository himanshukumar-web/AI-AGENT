"""
JARVIS AI — Specialized Planner Agent
Decomposes complex, multi-faceted user requests into a structured TaskGraph (DAG).
Identifies dependencies, execution order, and opportunities for parallel execution.
"""

import json
from typing import Any, Dict, List
from AGENTS.core.agent import BaseAgent
from AGENTS.core.agent_context import AgentContext
from AGENTS.core.agent_result import AgentResult
from BRAIN.LLM.provider_manager import provider_manager


class PlannerAgent(BaseAgent):
    """Specialized agent that decomposes complex requests into a dependency-ordered plan."""

    def __init__(self):
        super().__init__(
            name="planner",
            description="Decomposes requests into subtasks with dependencies, ordering, and parallel branch opportunities.",
            capabilities=["task_decomposition", "plan_generation", "dependency_mapping", "parallelization"],
            allowed_tools=[],
            risk_level="LOW",
            max_steps=2,
            timeout=30.0,
        )

    def execute(self, context: AgentContext) -> AgentResult:
        """Analyze request and generate task decomposition."""
        request = context.get_input("request", context.user_request)

        can_llm, _ = context.budget_tracker.can_call_llm()
        if can_llm:
            try:
                context.budget_tracker.record_llm_call()
                plan_data = self._plan_with_llm(request)
                if plan_data and plan_data.get("tasks"):
                    return AgentResult.ok(output=plan_data, metadata={"planner": "llm"})
            except Exception:
                pass

        # Robust Heuristic Decomposition
        plan_data = self._plan_heuristically(request)
        return AgentResult.ok(output=plan_data, metadata={"planner": "heuristic"})

    def _plan_with_llm(self, request: str) -> Dict[str, Any]:
        """Use LLM to generate structured task graph representation."""
        prompt = f"""You are the Master Planner for JARVIS AI. Decompose the following multi-step user request into discrete tasks assigned to specialized agents.
Available Agents:
- research: search, extract, compare, report, citations
- automation: scheduled workflows, reminders, youtube
- browser: open URL, web search, page inspection
- computer: vision, mouse, keyboard, windows
- system: time, battery, weather, app launch
- memory: remember facts, recall preferences
- conversation: natural language explanation

USER REQUEST: {request}

Return ONLY valid JSON (no markdown fences, no explanatory text) with this format:
{{
  "title": "Short title",
  "tasks": [
    {{
      "id": "task_1",
      "agent": "research",
      "action": "research",
      "description": "Short description",
      "inputs": {{"query": "..."}},
      "dependencies": []
    }},
    {{
      "id": "task_2",
      "agent": "automation",
      "action": "create",
      "description": "Short description",
      "inputs": {{"name": "..."}},
      "dependencies": ["task_1"]
    }}
  ]
}}
"""
        active_prov = provider_manager.get_active_provider()
        if active_prov.provider_name == "offline_fallback":
            return {}

        resp = active_prov.generate(prompt, temperature=0.2, max_tokens=512)
        text = resp.text.strip() if resp and resp.text else ""
        if "```" in text:
            lines = [l for l in text.split("\n") if not l.startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)

    def _plan_heuristically(self, request: str) -> Dict[str, Any]:
        """Decompose common multi-intent composite requests deterministically."""
        r = request.lower()
        tasks: List[Dict[str, Any]] = []

        # Example: "Find the best Python courses for me, compare them, create a study plan, save it, and remind me every morning"
        if "course" in r or "tutorial" in r:
            tasks.append({
                "id": "task_1",
                "agent": "research",
                "action": "research",
                "description": "Research Python courses and tutorials",
                "inputs": {"query": "best Python courses tutorials 2026", "mode": "standard"},
                "dependencies": [],
            })
            tasks.append({
                "id": "task_2",
                "agent": "research",
                "action": "compare",
                "description": "Compare top learning options",
                "inputs": {"query": "compare Python courses", "entities": ["Coursera", "freeCodeCamp", "Official Python Docs"]},
                "dependencies": ["task_1"],
            })
            tasks.append({
                "id": "task_3",
                "agent": "memory",
                "action": "store",
                "description": "Save study plan in memory",
                "inputs": {"key": "python_study_plan", "value": "Coursera, freeCodeCamp, Official Python Docs", "category": "fact"},
                "dependencies": ["task_2"],
            })
            if "remind" in r or "every morning" in r or "schedule" in r:
                tasks.append({
                    "id": "task_4",
                    "agent": "automation",
                    "action": "create",
                    "description": "Schedule daily study reminder",
                    "inputs": {"name": "Daily Python Study", "action_name": "speak_text", "schedule_time": "09:00"},
                    "dependencies": ["task_3"],
                })
            return {"title": "Python Study Plan & Daily Reminder", "tasks": tasks}

        # General Comparison & Report
        if "compare" in r:
            tasks.append({
                "id": "task_1",
                "agent": "research",
                "action": "compare",
                "description": "Execute comparison analysis",
                "inputs": {"query": request},
                "dependencies": [],
            })
            tasks.append({
                "id": "task_2",
                "agent": "memory",
                "action": "store",
                "description": "Save comparison results in memory",
                "inputs": {"key": "last_comparison", "value": f"Comparison of {request}", "category": "fact"},
                "dependencies": ["task_1"],
            })
            return {"title": "Comparative Analysis Task", "tasks": tasks}

        # Fallback single general task
        tasks.append({
            "id": "task_1",
            "agent": "conversation",
            "action": "chat",
            "description": "Process user instruction",
            "inputs": {"prompt": request},
            "dependencies": [],
        })
        return {"title": "Direct Request", "tasks": tasks}
