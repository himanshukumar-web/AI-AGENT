"""
JARVIS AI — Core Agent Brain & Layered Intelligence (Phase 2)
Orchestrates Router, Planner, Namespaced Tools, Memory 2.0, Task State, and LLM Reasoning.
"""

import json
import os
import random
import re
import sys
import time
from typing import Any, Dict, Generator, List, Optional
from colorama import Fore

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    PATHS, import_module_from_path, USER_NAME, ASSISTANT_NAME,
    LLM_ROUTING_MODE, LLM_TEMPERATURE, LLM_MAX_TOKENS
)
from BRAIN.LLM.provider_manager import provider_manager
from BRAIN.TOOLS.tool_registry import tool_registry
from BRAIN.MEMORY.conversation_manager import conversation_manager
from BRAIN.MEMORY.memory_manager import memory_manager
from BRAIN.PROMPTS.system_prompt import get_system_prompt
from BRAIN.CORE_AGENT.router import intelligent_router, RouteCategory
from BRAIN.CORE_AGENT.task_state import task_state_manager, TaskState
from BRAIN.PLANNER.planner import task_planner
from BRAIN.UTILS.logger import jarvis_logger
from BRAIN.UTILS.metrics import metrics_tracker


class AgentBrain:
    """Modern layered AI agent orchestrator."""

    def __init__(self):
        self._load_legacy_subsystems()

    def _load_legacy_subsystems(self):
        """Safely import legacy utilities and dialog data."""
        try:
            dlg = import_module_from_path('DLG', PATHS['dlg'])
            self.res1 = getattr(dlg, 'res1', ["Hello sir, Jarvis is online."])
            self.res_bye = getattr(dlg, 'res_bye', ["Goodbye sir. Have a wonderful day."])
            self.stopdlg = getattr(dlg, 'stopdlg', ["Going to sleep sir."])
            self.cmd1 = getattr(dlg, 'cmd1', ["hello", "hi", "jarvis", "hey jarvis"])
            self.stopcmd = getattr(dlg, 'stopcmd', ["stop listening", "go to sleep", "sleep"])
            self.bye_key_word = getattr(dlg, 'bye_key_word', ["goodbye", "bye", "exit", "quit"])
        except Exception:
            self.res1 = ["Hello sir, Jarvis is online."]
            self.res_bye = ["Goodbye sir. Have a wonderful day."]
            self.stopdlg = ["Going to sleep sir."]
            self.cmd1 = ["hello", "hi", "jarvis", "hey jarvis"]
            self.stopcmd = ["stop listening", "go to sleep", "sleep"]
            self.bye_key_word = ["goodbye", "bye", "exit", "quit"]

        # Q&A Dataset
        self.qa_dict = {}
        qa_path = PATHS.get('qna_txt', '')
        if os.path.exists(qa_path):
            try:
                with open(qa_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line and ':' in line:
                            parts = line.split(":", 1)
                            self.qa_dict[parts[0].strip().lower()] = parts[1].strip()
            except Exception:
                pass

        # ML Model 2 (Naive Bayes)
        try:
            modal2 = import_module_from_path('modal_2', PATHS['modal_2'])
            self.ml2_response = modal2.get_response
        except Exception:
            self.ml2_response = None

        # ML Model 1 (TF-IDF)
        try:
            modal1 = import_module_from_path('modal_1', PATHS['modal_1'])
            self.ml1_response = modal1.mind
        except Exception:
            self.ml1_response = None

    def normalize_command(self, text: str) -> str:
        """Strip wake words and conversational filler prefixes."""
        if not text:
            return ""
        t = text.lower().strip()
        t = re.sub(r'\b(jarvis|hey jarvis|ok jarvis|okay jarvis|hello jarvis)\b', '', t).strip()

        prefixes = [
            "could you please", "can you please", "would you please",
            "could you", "can you", "would you", "will you",
            "please", "kindly", "i want you to",
            "help me to", "help me", "do me a favor and",
        ]
        for p in sorted(prefixes, key=len, reverse=True):
            if t.startswith(p + " "):
                t = t[len(p):].strip()

        suffixes = [
            "for me please", "for me", "please", "right now",
            "now", "quickly", "asap",
        ]
        for s in sorted(suffixes, key=len, reverse=True):
            if t.endswith(" " + s):
                t = t[:-len(s)].strip()

        return t

    def _handle_memory_command(self, meta: Dict[str, Any]) -> str:
        """Process natural memory commands directly."""
        sub_type = meta.get("sub_type")
        if sub_type == "remember":
            content = meta.get("content", "")
            # Attempt to split on key/value if contains 'that' or ':'
            parts = content.split("is", 1) if "is" in content else content.split(":", 1)
            if len(parts) == 2:
                k = parts[0].replace("my", "").replace("that", "").strip()
                v = parts[1].strip()
            else:
                k = f"note_{int(time.time())}"
                v = content.strip()
            memory_manager.store_fact(key=k, value=v, category="preference")
            return f"Understood {USER_NAME}, I'll remember that {k} is {v}."

        if sub_type == "forget":
            query = meta.get("query", "")
            count = memory_manager.forget_facts_matching(query)
            if count > 0:
                return f"I have forgotten {count} memory record{'s' if count != 1 else ''} regarding '{query}'."
            return f"I couldn't find any memory records matching '{query}' to forget."

        if sub_type == "recall":
            facts = memory_manager.recall_facts(category="preference")
            if not facts:
                return f"I don't have any specific preferences saved in my memory yet, {USER_NAME}."
            summary = ", ".join([f"{f['key']}: {f['value']}" for f in facts[:5]])
            return f"Here is what I remember about your preferences: {summary}."

        return "Memory operation completed."

    def _handle_research_command(self, meta: Dict[str, Any], raw_text: str) -> str:
        """Process web research, comparison, follow-up, and monitoring commands."""
        sub_type = meta.get("sub_type", "research")

        if sub_type == "save_research":
            try:
                from WEB.research.memory import research_memory
                last = research_memory.get_last_session()
                if last:
                    return f"I have saved your research session on '{last.get('title')}' to persistent research memory, {USER_NAME}."
                return f"No active research session to save right now, {USER_NAME}."
            except Exception as e:
                return f"Unable to save research: {e}"

        if sub_type == "continue_research":
            try:
                from WEB.research.memory import research_memory
                from WEB.research.planner import research_planner, ResearchMode
                last = research_memory.get_last_session()
                if last:
                    target = f"{last.get('query')} latest documentation and updates 2026"
                    res = research_planner.plan_and_execute(target, mode=ResearchMode.STANDARD)
                    return f"Continuing previous research on '{last.get('title')}': {res.summary}"
                return f"I couldn't find a previous research session to continue, {USER_NAME}."
            except Exception as e:
                return f"Error continuing research: {e}"

        if sub_type == "check_changed":
            try:
                from WEB.research.monitor import source_monitor
                res = source_monitor.check_for_changes(meta.get("query"))
                return res.get("summary", "Source monitoring complete.")
            except Exception as e:
                return f"Error checking for updates: {e}"

        if sub_type == "compare":
            try:
                from WEB.research.planner import research_planner, ResearchMode
                res = research_planner.plan_and_execute(raw_text, mode=ResearchMode.STANDARD)
                if res.comparison_table:
                    print(f"\n{res.comparison_table}\n")
                return res.summary
            except Exception as e:
                return f"Error conducting comparison: {e}"

        # Standard / Quick / Deep Research
        try:
            from WEB.research.planner import research_planner, ResearchMode
            query = meta.get("query") or raw_text
            mode_str = meta.get("mode", "standard")
            m = ResearchMode.DEEP if mode_str == "deep" else (ResearchMode.QUICK if mode_str == "quick" else ResearchMode.STANDARD)
            res = research_planner.plan_and_execute(query, mode=m)

            if res.cancelled:
                return "Research was cancelled, sir."

            if res.full_report and mode_str == "deep":
                print(f"\n{res.full_report}\n")

            if res.key_findings and len(res.key_findings) > 1:
                findings_preview = "\n".join(f"- {f}" for f in res.key_findings[:3])
                return f"{res.summary}\n\nKey Findings:\n{findings_preview}"
            return res.summary
        except Exception as e:
            return f"Research encountered an error: {e}"

    def _try_fast_deterministic_path(self, raw_text: str, norm_text: str) -> Optional[str]:
        """
        Fast path: Instant local execution without LLM latency for unambiguous commands.
        """
        if not norm_text:
            return random.choice(self.res1)

        # 1. Greetings
        if raw_text in [c.lower() for c in self.cmd1] or norm_text in [c.lower() for c in self.cmd1] or norm_text in ["hi", "hello", "hey", "namaste"]:
            return random.choice(self.res1)

        # 2. Goodbye / Exit
        if norm_text in [b.lower() for b in self.bye_key_word] or any(bw in norm_text for bw in ["goodbye", "bye", "exit", "quit", "alvida"]):
            return random.choice(self.res_bye)

        # 3. Sleep
        if norm_text in [s.lower() for s in self.stopcmd] or any(s in norm_text for s in ["go to sleep", "stop listening", "so jao"]):
            return random.choice(self.stopdlg)

        # 4. Diagnostics command
        if norm_text in ["run diagnostics", "diagnostics", "check health", "doctor", "health check"]:
            res = tool_registry.execute_tool("system.diagnostics", user_request=raw_text)
            return "Diagnostics check completed and displayed on your console."

        # 5. Recent Actions
        if norm_text in ["show my recent actions", "show recent actions", "recent actions", "action history", "show actions"]:
            res = tool_registry.execute_tool("action.history", {"limit": 5}, user_request=raw_text)
            if res.get("success"):
                actions = res["data"]["actions"]
                if not actions:
                    return "No recent actions recorded yet."
                summary = ", ".join([f"{a['tool_name']} ({'OK' if a['success'] else 'Failed'})" for a in actions[:3]])
                return f"Recent actions: {summary}."

        # 6. Capabilities & Skills ("what can you do?")
        if norm_text in ["what can you do", "what are your capabilities", "capabilities", "what are your skills", "show skills", "skills", "help"]:
            try:
                from SKILLS.skill_registry import skill_registry
                return skill_registry.get_capabilities_summary()
            except Exception:
                return "I can help you with web browsing, YouTube playback, system controls, automations, memory, and multi-step research."

        # 7. Operational Status ("Jarvis, status")
        if norm_text in ["status", "jarvis status", "system status", "system summary"]:
            res = tool_registry.execute_tool("system.status", user_request=raw_text)
            if res.get("success"):
                return res["data"].get("formatted", "System status is healthy and operational.")
            return "JARVIS systems are online and operational."

        # 8. Active Task Queries ("show my current task", "what are you doing")
        if norm_text in ["show my current task", "show current task", "current task", "what are you doing", "task status"]:
            try:
                from BRAIN.CORE_AGENT.task_manager import task_manager
                return task_manager.get_status_summary()
            except Exception:
                return "No active background tasks are currently running."

        if norm_text in ["cancel the task", "cancel current task", "cancel task", "abort task"]:
            try:
                from BRAIN.CORE_AGENT.task_manager import task_manager
                cancelled = task_manager.cancel_current_task()
                task_state_manager.request_interruption()
                return "The active task has been cancelled." if cancelled else "No active task to cancel."
            except Exception:
                return "Task cancelled."



        # 6. Time
        if norm_text in ["what time is it", "what is the time", "current time", "tell me time", "time batao", "kitne baje", "kya time hai"]:
            res = tool_registry.execute_tool("system.time", user_request=raw_text)
            if res.get("success"):
                return f"The current time is {res['data']['time']}."

        # 7. Battery
        if norm_text in ["battery", "battery status", "battery percentage", "check battery", "battery kitni hai", "what is the battery percentage"]:
            res = tool_registry.execute_tool("system.battery", user_request=raw_text)
            if res.get("success"):
                return res['data']['formatted']

        # 8. Weather
        if norm_text in ["weather", "how is the weather", "tell me the weather", "mausam batao", "weather batao", "check weather", "how's the weather"]:
            res = tool_registry.execute_tool("weather.get", user_request=raw_text)
            if res.get("success"):
                return f"It is currently {res['data']['formatted']}."

        # 9. Joke
        if norm_text in ["tell me a joke", "joke", "make me laugh", "funny", "joke sunao"]:
            res = tool_registry.execute_tool("system.joke", user_request=raw_text)
            if res.get("success"):
                return res['data']['joke']

        # 10. Advice
        if norm_text in ["give me advice", "advice", "suggestion", "motivate me", "advice do"]:
            res = tool_registry.execute_tool("system.advice", user_request=raw_text)
            if res.get("success"):
                return f"Here is a thought: {res['data']['advice']}"

        # 11. IP Address & Internet
        if norm_text in ["my ip", "ip address", "find my ip", "what is my ip"]:
            res = tool_registry.execute_tool("system.ip", user_request=raw_text)
            if res.get("success"):
                return f"Your public IP is {res['data']['ip']}."

        if norm_text in ["internet status", "am i online", "check internet", "internet"]:
            res = tool_registry.execute_tool("system.internet", user_request=raw_text)
            if res.get("success"):
                return res['data']['status']

        # 12. Direct Website Launch
        if norm_text in ["open youtube", "youtube open", "youtube kholo"]:
            tool_registry.execute_tool("browser.open", {"url": "youtube.com"}, user_request=raw_text)
            conversation_manager.set_context_state(active_topic="youtube", last_action="browser.open")
            return "Opening YouTube."

        if norm_text in ["open google", "google open", "google kholo"]:
            tool_registry.execute_tool("browser.open", {"url": "google.com"}, user_request=raw_text)
            conversation_manager.set_context_state(active_topic="browser", last_action="browser.open")
            return "Opening Google."

        if norm_text in ["open github", "github open", "github kholo"]:
            tool_registry.execute_tool("browser.open", {"url": "github.com"}, user_request=raw_text)
            conversation_manager.set_context_state(active_topic="browser", last_action="browser.open")
            return "Opening GitHub."

        # 13. Application Launching
        if norm_text.startswith("open notepad") or norm_text == "notepad kholo":
            tool_registry.execute_tool("system.launch_app", {"app_name": "notepad"}, user_request=raw_text)
            return "Opening Notepad."

        if norm_text.startswith("open calculator") or norm_text in ["calc kholo", "open calc"]:
            tool_registry.execute_tool("system.launch_app", {"app_name": "calc"}, user_request=raw_text)
            return "Opening Calculator."

        # 14. YouTube Search & Controls
        if norm_text.startswith(("search youtube for ", "search on youtube for ", "youtube search ")):
            query = norm_text.replace("search youtube for ", "").replace("search on youtube for ", "").replace("youtube search ", "").strip()
            res = tool_registry.execute_tool("youtube.search", {"query": query}, user_request=raw_text)
            if res.get("success"):
                return f"Searching YouTube for {query}."

        if norm_text in ["pause youtube", "resume youtube", "pause video", "resume video", "play pause"]:
            tool_registry.execute_tool("youtube.pause", user_request=raw_text)
            return "Toggled playback."

        # 15. Automations List
        if norm_text in ["show my automations", "show automations", "list automations", "list my automations", "my automations"]:
            res = tool_registry.execute_tool("automation.list", user_request=raw_text)
            if res.get("success"):
                autos = res["data"]["automations"]
                if not autos:
                    return "You don't have any configured automations yet."
                names = ", ".join([f"{a['name']} ({a['schedule_time'] or 'Manual'})" for a in autos[:4]])
                return f"Your automations: {names}."

        # 16. Contextual Ordinal Follow-up (e.g. "play the second result" / "play the 2nd one")
        if any(w in norm_text for w in ["play the", "play second", "play 2nd", "play first", "play 1st", "play third", "play 3rd"]):
            idx = conversation_manager.resolve_ordinal_index(norm_text)
            if idx is not None:
                search_results = conversation_manager.get_search_results()
                if search_results and idx < len(search_results):
                    target_song = search_results[idx]
                    tool_registry.execute_tool("youtube.play", {"query": target_song}, user_request=raw_text)
                    return f"Playing option {idx + 1}: {target_song}."

        # 17. Exact QNA Dataset match
        if norm_text in self.qa_dict:
            return self.qa_dict[norm_text]

        # 18. Computer Vision & Desktop Perception
        if norm_text in ["what is on my screen", "what's on my screen", "describe what is on my screen", "describe my screen", "screen pe kya hai", "what do you see on my screen"]:
            res = tool_registry.execute_tool("computer.analyze_screen", user_request=raw_text)
            if res.get("success"):
                return res["data"].get("summary", "Screen analyzed.")
            return "Unable to analyze the screen."

        if norm_text in ["what application is open", "what app is open", "which app is open", "which window is open", "active application"]:
            res = tool_registry.execute_tool("computer.get_active_window", user_request=raw_text)
            if res.get("success"):
                title = res["data"].get("title", "Unknown")
                app = res["data"].get("app_name", "Unknown")
                return f"Currently active: {app} with window '{title}'."
            return "Unable to determine the active application."

        if norm_text in ["what can you do with my computer", "computer capabilities", "what can you do on my computer"]:
            try:
                from SKILLS.computer_skill import ComputerSkill
                skill = ComputerSkill()
                return "Here are my computer control capabilities:\n" + "\n".join(f"- {c}" for c in skill.get_capabilities_list())
            except Exception:
                return "I can perceive your screen, locate UI elements, manage windows, and execute controlled mouse and keyboard actions with safety bounds."

        if norm_text in ["scroll down", "niche scroll karo"]:
            tool_registry.execute_tool("computer.scroll", {"clicks": -5}, user_request=raw_text)
            return "Scrolled down."

        if norm_text in ["scroll up", "upar scroll karo"]:
            tool_registry.execute_tool("computer.scroll", {"clicks": 5}, user_request=raw_text)
            return "Scrolled up."

        return None


    def process_command(self, text: str) -> Optional[str]:
        """
        Main entry point for processing a text command.
        Executes layered pipeline: Router -> Fast Path / Planner / Memory / LLM Agent -> Fallbacks.
        """
        if not text or not str(text).strip():
            return None

        raw_text = str(text).strip()
        norm_text = self.normalize_command(raw_text)

        # Record user turn
        conversation_manager.add_user_message(raw_text)

        # 1. Routing Phase
        context_state = conversation_manager.get_context_state()
        category, meta = intelligent_router.route(norm_text, active_topic=context_state.get("active_topic"))
        jarvis_logger.info("ROUTER", f"Classified input as [{category.name}]")

        # 2. Interruption Handler
        if category == RouteCategory.INTERRUPT:
            task_state_manager.request_interruption()
            msg = "Action stopped, sir."
            conversation_manager.add_assistant_message(msg)
            return msg

        # 3. Memory 2.0 Command Direct Handler
        if category == RouteCategory.MEMORY_COMMAND:
            msg = self._handle_memory_command(meta)
            conversation_manager.add_assistant_message(msg)
            return msg

        # 3.5. Web Intelligence & Deep Research Handler
        if category == RouteCategory.SEARCH_RESEARCH:
            jarvis_logger.info("AGENT", "Routing to Web Intelligence & Deep Research Planner")
            msg = self._handle_research_command(meta, raw_text)
            conversation_manager.add_assistant_message(msg)
            return msg

        # 4. Fast Deterministic Path (0 LLM latency)
        if category == RouteCategory.SIMPLE_COMMAND or LLM_ROUTING_MODE == "fast_first":
            fast_res = self._try_fast_deterministic_path(raw_text.lower(), norm_text)
            if fast_res is not None:
                conversation_manager.add_assistant_message(fast_res)
                return fast_res

        # 5. Multi-Agent Orchestrator & Multi-Step Task Planner (Phase 7)
        if category == RouteCategory.MULTI_STEP_TASK:
            try:
                from config import AGENT_SYSTEM_ENABLED
                if AGENT_SYSTEM_ENABLED:
                    from AGENTS.orchestrator import agent_orchestrator
                    jarvis_logger.info("AGENT", "Delegating complex instruction to Multi-Agent Orchestrator")
                    ans = agent_orchestrator.handle_request(raw_text)
                    conversation_manager.add_assistant_message(ans)
                    return ans
            except Exception as e:
                jarvis_logger.warning("AGENT", f"Multi-Agent Orchestrator fallback to TaskPlanner: {e}")

            jarvis_logger.info("AGENT", "Delegating complex instruction to Task Planner")
            plan = task_planner.create_plan(raw_text)
            exec_res = task_planner.execute_plan(plan)
            if exec_res.get("interrupted"):
                ans = "Task was interrupted and safely stopped."
            else:
                ans = f"I've completed the task '{plan.title}'. {exec_res.get('summary', '')}"
            conversation_manager.add_assistant_message(ans)
            return ans

        # 6. Modern LLM Agent with Grounded Tool Invocation
        active_provider = provider_manager.get_active_provider()
        if active_provider.provider_name != "offline_fallback" and LLM_ROUTING_MODE != "offline_only":
            try:
                # Memory relevance injection
                relevant_facts = memory_manager.search_relevant_context(raw_text)
                system_prompt = get_system_prompt(custom_facts=relevant_facts)
                history = conversation_manager.get_history_for_llm()[:-1]
                tools = tool_registry.get_contextual_tools(query=norm_text, active_topic=context_state.get("active_topic"))

                # Step 1: Initial LLM inference
                start_llm = time.perf_counter()
                llm_response = provider_manager.generate_with_fallback(
                    prompt=raw_text,
                    system_prompt=system_prompt,
                    history=history,
                    tools=tools,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS,
                )

                duration_ms = (time.perf_counter() - start_llm) * 1000.0
                usage = getattr(llm_response, 'usage', {}) or {}
                metrics_tracker.record_llm_call(
                    duration_ms=duration_ms,
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0)
                )

                # Step 2: Handle Tool Calls
                if llm_response.has_tool_calls:
                    tool_results = []
                    for tc in llm_response.tool_calls:
                        res = tool_registry.execute_tool(tc.name, tc.arguments, user_request=raw_text)
                        tool_results.append({"tool": tc.name, "arguments": tc.arguments, "result": res})
                        # Update context state
                        if "youtube" in tc.name:
                            conversation_manager.set_context_state(active_topic="youtube", last_action=tc.name)
                        elif "weather" in tc.name:
                            conversation_manager.set_context_state(active_topic="weather", last_action=tc.name)
                        elif "automation" in tc.name:
                            conversation_manager.set_context_state(active_topic="automation", last_action=tc.name)

                    # Step 3: Synthesis with grounded tool observation
                    obs_prompt = f"User Request: {raw_text}\nTool Execution Results:\n{json.dumps(tool_results, indent=2)}\nProvide a helpful, direct, concise spoken response to {USER_NAME} based strictly on these actual tool results."
                    final_response = provider_manager.generate_with_fallback(
                        prompt=obs_prompt,
                        system_prompt=system_prompt,
                        history=history,
                        temperature=0.5,
                        max_tokens=256,
                    )
                    ans = final_response.text.strip()
                    conversation_manager.add_assistant_message(ans, tool_calls=llm_response.tool_calls)
                    return ans

                if llm_response.text and llm_response.text.strip():
                    ans = llm_response.text.strip()
                    conversation_manager.add_assistant_message(ans)
                    return ans

            except Exception as e:
                jarvis_logger.warning("AGENT", f"LLM error: {e}. Falling back...")

        # 7. Legacy ML Models & Search Fallback
        if self.ml2_response is not None:
            try:
                ml2_res = self.ml2_response(norm_text)
                if ml2_res:
                    conversation_manager.add_assistant_message(ml2_res)
                    return ml2_res
            except Exception:
                pass

        if self.ml1_response is not None:
            try:
                ml1_res = self.ml1_response(norm_text)
                if ml1_res:
                    conversation_manager.add_assistant_message(ml1_res)
                    return ml1_res
            except Exception:
                pass

        # 8. Default Friendly Fallback
        fallback_msg = f"I've noted that {USER_NAME}. Let me know if you would like me to assist with anything else."
        conversation_manager.add_assistant_message(fallback_msg)
        return fallback_msg

    def process_command_stream(self, text: str) -> Generator[str, None, None]:
        """Stream response for CLI mode."""
        response = self.process_command(text)
        if response:
            words = response.split(" ")
            for i, w in enumerate(words):
                yield w + (" " if i < len(words) - 1 else "")


# Global singleton instance
agent_brain = AgentBrain()
