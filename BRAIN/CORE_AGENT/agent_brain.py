"""
JARVIS AI — Core Agent Brain & Layered Intelligence
Orchestrates Fast Path Detection, Legacy ML/Q&A fallback, LLM Reasoning, Tool Execution, and Memory.
"""

import json
import os
import random
import re
import sys
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


class AgentBrain:
    """Modern layered AI agent orchestrator."""

    def __init__(self):
        self._load_legacy_subsystems()

    def _load_legacy_subsystems(self):
        """Safely import legacy utilities and dialog data."""
        # DLG
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

    def _try_fast_deterministic_path(self, raw_text: str, norm_text: str) -> Optional[str]:
        """
        Fast path: Instant local execution without LLM latency for unambiguous commands.
        """
        if not norm_text:
            return random.choice(self.res1)

        # 1. Greetings
        if raw_text in [c.lower() for c in self.cmd1] or norm_text in [c.lower() for c in self.cmd1] or norm_text in ["hi", "hello", "hey"]:
            return random.choice(self.res1)

        # 2. Goodbye / Exit
        if norm_text in [b.lower() for b in self.bye_key_word] or any(bw in norm_text for bw in ["goodbye", "bye", "exit", "quit"]):
            return random.choice(self.res_bye)

        # 3. Sleep
        if norm_text in [s.lower() for s in self.stopcmd] or any(s in norm_text for s in ["go to sleep", "stop listening"]):
            return random.choice(self.stopdlg)

        # 4. Time
        if norm_text in ["what time is it", "what is the time", "current time", "tell me time", "time batao", "kitne baje"]:
            res = tool_registry.execute_tool("get_time")
            if res.get("success"):
                return f"The current time is {res['data']['time']}."

        # 5. Battery
        if norm_text in ["battery", "battery status", "battery percentage", "check battery", "battery kitni hai"]:
            res = tool_registry.execute_tool("get_battery_status")
            if res.get("success"):
                return res['data']['formatted']

        # 6. Joke
        if norm_text in ["tell me a joke", "joke", "make me laugh", "funny"]:
            res = tool_registry.execute_tool("get_joke")
            if res.get("success"):
                return res['data']['joke']

        # 7. Advice
        if norm_text in ["give me advice", "advice", "suggestion", "motivate me"]:
            res = tool_registry.execute_tool("get_advice")
            if res.get("success"):
                return f"Here is some advice: {res['data']['advice']}"

        # 8. IP Address
        if norm_text in ["my ip", "ip address", "find my ip", "what is my ip"]:
            res = tool_registry.execute_tool("get_ip")
            if res.get("success"):
                return f"Your public IP is {res['data']['ip']}."

        # 9. Direct Single App / Website Launch (e.g. "open youtube", "open google", "open notepad")
        if norm_text == "open youtube":
            tool_registry.execute_tool("open_website", {"url": "youtube.com"})
            conversation_manager.set_context_state(active_topic="youtube", last_action="open_website")
            return "Opening YouTube, sir."

        if norm_text == "open google":
            tool_registry.execute_tool("open_website", {"url": "google.com"})
            conversation_manager.set_context_state(active_topic="browser", last_action="open_website")
            return "Opening Google, sir."

        if norm_text.startswith("open notepad"):
            tool_registry.execute_tool("launch_application", {"app_name": "notepad"})
            return "Opening Notepad, sir."

        if norm_text.startswith("open calculator"):
            tool_registry.execute_tool("launch_application", {"app_name": "calc"})
            return "Opening Calculator, sir."

        # 10. Exact QNA Dataset match
        if norm_text in self.qa_dict:
            return self.qa_dict[norm_text]

        return None

    def process_command(self, text: str) -> Optional[str]:
        """
        Main entry point for processing a text command.
        Executes layered pipeline: Fast Path -> LLM Reasoner + Tools -> Fallbacks.
        """
        if not text or not str(text).strip():
            return None

        raw_text = str(text).strip()
        norm_text = self.normalize_command(raw_text)

        # Record user turn
        conversation_manager.add_user_message(raw_text)

        # Layer 1: Fast Deterministic Path (if routing mode is hybrid or fast_first)
        if LLM_ROUTING_MODE in ("hybrid", "fast_first"):
            fast_res = self._try_fast_deterministic_path(raw_text.lower(), norm_text)
            if fast_res is not None:
                conversation_manager.add_assistant_message(fast_res)
                return fast_res

        # Layer 2: Modern LLM Agent with Tool Invocation
        active_provider = provider_manager.get_active_provider()
        if active_provider.provider_name != "offline_fallback" and LLM_ROUTING_MODE != "offline_only":
            try:
                # Prepare context
                facts_list = memory_manager.recall_facts(category="preference")
                facts_str = "\n".join([f"- {f['key']}: {f['value']}" for f in facts_list])
                system_prompt = get_system_prompt(custom_facts=facts_str)
                history = conversation_manager.get_history_for_llm()[:-1]  # Exclude current prompt from history
                tools = tool_registry.get_tool_definitions()

                # Step 1: Initial LLM inference
                llm_response = provider_manager.generate_with_fallback(
                    prompt=raw_text,
                    system_prompt=system_prompt,
                    history=history,
                    tools=tools,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS,
                )

                # Step 2: Handle Tool Calls
                if llm_response.has_tool_calls:
                    tool_results = []
                    for tc in llm_response.tool_calls:
                        res = tool_registry.execute_tool(tc.name, tc.arguments)
                        tool_results.append({"tool": tc.name, "arguments": tc.arguments, "result": res})
                        # Update context state
                        if "youtube" in tc.name:
                            conversation_manager.set_context_state(active_topic="youtube", last_action=tc.name)
                        elif "weather" in tc.name:
                            conversation_manager.set_context_state(active_topic="weather", last_action=tc.name)
                        elif "automation" in tc.name:
                            conversation_manager.set_context_state(active_topic="automation", last_action=tc.name)

                    # Step 3: Second-pass synthesis with tool observation
                    obs_prompt = f"User Request: {raw_text}\nTool Execution Results:\n{json.dumps(tool_results, indent=2)}\nProvide a helpful, direct, concise spoken response to {USER_NAME} based on these actual tool results."
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
                print(Fore.YELLOW + f"  [Agent LLM Error] {e}. Falling back to internal engine...")

        # Layer 3: Legacy ML Intent & QA Fallback
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

        # Layer 4: Default Fallback
        fallback_msg = "I understand, sir. Let me know if you would like me to perform any further action."
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
