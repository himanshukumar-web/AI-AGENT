"""
JARVIS AI — Comprehensive Verification & Phase 2 Advanced Agent Test Suite
Tests all core subsystems, Router, Planner, Namespaced Tools, Memory 2.0, Action Logger, and Doctor.
"""

import os
import sys
import unittest
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import PATHS, import_module_from_path, USER_NAME, ASSISTANT_NAME, LLM_PROVIDER
from BRAIN.LLM.base_provider import BaseLLMProvider, LLMResponse, ToolCall
from BRAIN.LLM.provider_manager import provider_manager
from BRAIN.TOOLS.tool_registry import tool_registry
from BRAIN.TOOLS.safety_manager import safety_manager, RiskLevel
from BRAIN.TOOLS.action_logger import action_logger
from BRAIN.MEMORY.memory_manager import MemoryManager, memory_manager
from BRAIN.MEMORY.conversation_manager import conversation_manager
from BRAIN.CORE_AGENT.router import intelligent_router, RouteCategory
from BRAIN.CORE_AGENT.task_state import task_state_manager, TaskState
from BRAIN.PLANNER.planner import task_planner, TaskPlan, PlanStep
from BRAIN.UTILS.diagnostics import doctor
from BRAIN.UTILS.metrics import metrics_tracker
from BRAIN.PROMPTS.system_prompt import get_system_prompt
from VOICE.voice_engine import voice_engine


class TestJarvisConfig(unittest.TestCase):
    def test_paths_exist(self):
        """Verify all critical files exist in declared paths."""
        for name, path in PATHS.items():
            if name in ['automations_db', 'automation_logs']:
                continue  # Runtime files created on demand
            self.assertTrue(os.path.exists(path), f"Path does not exist: {path}")

    def test_config_variables(self):
        """Verify configuration constants."""
        self.assertIsInstance(USER_NAME, str)
        self.assertIsInstance(ASSISTANT_NAME, str)
        self.assertIsInstance(LLM_PROVIDER, str)


class TestIntelligentRouter(unittest.TestCase):
    def test_interruption_routing(self):
        """Test routing for user interruption."""
        cat, meta = intelligent_router.route("stop")
        self.assertEqual(cat, RouteCategory.INTERRUPT)
        cat, meta = intelligent_router.route("jarvis stop")
        self.assertEqual(cat, RouteCategory.INTERRUPT)

    def test_memory_routing(self):
        """Test routing for natural memory commands."""
        cat, meta = intelligent_router.route("remember that my favorite city is Tokyo")
        self.assertEqual(cat, RouteCategory.MEMORY_COMMAND)
        self.assertEqual(meta.get("sub_type"), "remember")

        cat, meta = intelligent_router.route("forget what I told you about Tokyo")
        self.assertEqual(cat, RouteCategory.MEMORY_COMMAND)
        self.assertEqual(meta.get("sub_type"), "forget")

        cat, meta = intelligent_router.route("what do you remember about my preferences?")
        self.assertEqual(cat, RouteCategory.MEMORY_COMMAND)
        self.assertEqual(meta.get("sub_type"), "recall")

    def test_simple_command_routing(self):
        """Test zero-latency simple command classification."""
        cat, meta = intelligent_router.route("what time is it")
        self.assertEqual(cat, RouteCategory.SIMPLE_COMMAND)

        cat, meta = intelligent_router.route("open youtube")
        self.assertEqual(cat, RouteCategory.SIMPLE_COMMAND)

    def test_multi_step_routing(self):
        """Test multi-step instruction detection."""
        cat, meta = intelligent_router.route("find the best python courses and summarize the result")
        self.assertEqual(cat, RouteCategory.MULTI_STEP_TASK)


class TestTaskPlanner(unittest.TestCase):
    def test_planner_creation_and_execution(self):
        """Test task planner generating and executing steps safely."""
        plan = task_planner.create_plan("Find the best Python courses, compare them and summarize the result")
        self.assertIsInstance(plan, TaskPlan)
        self.assertTrue(len(plan.steps) > 0)

        # Execute plan
        res = task_planner.execute_plan(plan)
        self.assertTrue(res.get("success"))
        self.assertFalse(res.get("interrupted"))

    def test_planner_interruption(self):
        """Test plan cancellation when interruption is signaled."""
        plan = TaskPlan(
            title="Interrupted Test Plan",
            steps=[
                PlanStep(tool="system.time", description="Check time"),
                PlanStep(tool="system.battery", description="Check battery"),
            ]
        )
        task_state_manager.request_interruption()
        res = task_planner.execute_plan(plan)
        self.assertTrue(res.get("interrupted"))
        task_state_manager.reset()


class TestNamespacedToolRegistry(unittest.TestCase):
    def test_canonical_and_aliased_tools(self):
        """Verify namespaced and legacy tool resolution."""
        canon = tool_registry.resolve_tool_name("get_time")
        self.assertEqual(canon, "system.time")

        canon = tool_registry.resolve_tool_name("youtube_play")
        self.assertEqual(canon, "youtube.play")

    def test_action_auditing(self):
        """Verify tool execution logs to action history."""
        res = tool_registry.execute_tool("system.time", user_request="Testing action audit")
        self.assertTrue(res["success"])

        actions = action_logger.get_recent_actions(limit=5)
        self.assertTrue(len(actions) > 0)
        self.assertEqual(actions[0]["tool_name"], "system.time")
        self.assertEqual(actions[0]["success"], 1)

    def test_action_history_and_diagnostics_tools(self):
        """Verify action.history and system.diagnostics tools execute cleanly."""
        res_hist = tool_registry.execute_tool("action.history", {"limit": 3})
        self.assertTrue(res_hist["success"])
        self.assertIn("actions", res_hist["data"])

        res_diag = tool_registry.execute_tool("system.diagnostics")
        self.assertTrue(res_diag["success"])
        self.assertIn("python", res_diag["data"])


class TestMemory2(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.mem = MemoryManager(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except Exception:
                pass

    def test_episodic_memory(self):
        """Test recording and recalling episodic tasks."""
        ok = self.mem.record_episode("Setup Development Workspace", "Opened IDE and cloned repositories", ["browser.open"])
        self.assertTrue(ok)

        episodes = self.mem.get_recent_episodes(limit=5)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["task_title"], "Setup Development Workspace")

    def test_relevance_retrieval(self):
        """Test scoring and selecting only relevant facts."""
        self.mem.store_fact("favorite_genre", "Synthwave", category="preference")
        self.mem.store_fact("favorite_editor", "VSCode", category="preference")
        self.mem.store_fact("home_city", "Berlin", category="preference")

        context = self.mem.search_relevant_context("play some synthwave music")
        self.assertIn("favorite_genre", context)
        self.assertIn("Synthwave", context)

    def test_forget_matching(self):
        """Test forgetting facts matching a query."""
        self.mem.store_fact("favorite_drink", "Matcha Tea")
        self.assertEqual(self.mem.get_fact("favorite_drink"), "Matcha Tea")

        count = self.mem.forget_facts_matching("matcha")
        self.assertEqual(count, 1)
        self.assertIsNone(self.mem.get_fact("favorite_drink"))

    def test_secret_redaction(self):
        """Verify memory manager rejects storing sensitive credentials and tokens."""
        saved_key = self.mem.store_fact("openai_api_key", "sk-1234567890abcdef")
        self.assertFalse(saved_key)
        self.assertIsNone(self.mem.get_fact("openai_api_key"))

        saved_pass = self.mem.store_fact("my_password", "supersecretpass")
        self.assertFalse(saved_pass)
        self.assertIsNone(self.mem.get_fact("my_password"))



class TestTaskStateAndInterruption(unittest.TestCase):
    def test_state_lifecycle(self):
        """Test task state transitions and interruption flag."""
        task_state_manager.reset()
        self.assertEqual(task_state_manager.state, TaskState.IDLE)

        task_state_manager.set_state(TaskState.PLANNING, "Complex Research")
        self.assertEqual(task_state_manager.state, TaskState.PLANNING)
        self.assertEqual(task_state_manager.current_task_name, "Complex Research")

        task_state_manager.request_interruption()
        self.assertEqual(task_state_manager.state, TaskState.INTERRUPTED)
        self.assertTrue(task_state_manager.is_interrupted())

        task_state_manager.reset()
        self.assertFalse(task_state_manager.is_interrupted())


class TestConversationFollowUp(unittest.TestCase):
    def test_ordinal_follow_up_resolution(self):
        """Test resolving 'play the second result' after YouTube search."""
        conversation_manager.reset()
        conversation_manager.set_search_results(["Song A - Artist 1", "Song B - Artist 2", "Song C - Artist 3"])

        idx = conversation_manager.resolve_ordinal_index("play the second result")
        self.assertEqual(idx, 1)

        idx_last = conversation_manager.resolve_ordinal_index("play the last one")
        self.assertEqual(idx_last, 2)


class TestJarvisDoctor(unittest.TestCase):
    def test_doctor_diagnostics(self):
        """Test doctor diagnostic health checks."""
        report = doctor.run_diagnostics()
        self.assertIn("python", report)
        self.assertIn("microphone", report)
        self.assertIn("tts", report)
        self.assertIn("internet", report)
        self.assertIn("llm", report)
        self.assertIn("memory_db", report)
        self.assertIn("automations", report)


class TestAgentBrain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain_mod = import_module_from_path('brain1', PATHS['brain1'])

    def test_command_normalizer(self):
        """Test natural language prefix and wake word stripping."""
        norm = self.brain_mod.normalize_command
        self.assertEqual(norm("Jarvis open youtube"), "open youtube")
        self.assertEqual(norm("please open notepad for me"), "open notepad")
        self.assertEqual(norm("can you please tell me a joke"), "tell me a joke")

    def test_fast_path_time(self):
        """Test fast path time check."""
        res = self.brain_mod.brain_cmd("what time is it")
        self.assertIsNotNone(res)
        self.assertTrue("current time is" in res.lower() or "time is" in res.lower())

    def test_fast_path_joke(self):
        """Test fast path joke."""
        res = self.brain_mod.brain_cmd("tell me a joke")
        self.assertIsNotNone(res)
        self.assertTrue(len(res) > 5)

    def test_fast_path_weather(self):
        """Test fast path weather."""
        res = self.brain_mod.brain_cmd("how is the weather")
        self.assertIsNotNone(res)
        self.assertTrue("weather" in res.lower() or "currently" in res.lower() or "°c" in res.lower())

    def test_hinglish_brain_routing(self):
        """Test Hinglish command direct execution in Brain."""
        res = self.brain_mod.brain_cmd("time batao")
        self.assertIsNotNone(res)
        self.assertTrue("time is" in res.lower())



class TestLLMProviders(unittest.TestCase):
    def test_provider_manager_initialization(self):
        """Verify provider manager discovers registered providers."""
        providers = provider_manager.list_available_providers()
        self.assertTrue(len(providers) >= 4)
        names = [p["provider"] for p in providers]
        self.assertIn("openai", names)
        self.assertIn("gemini", names)
        self.assertIn("ollama", names)
        self.assertIn("groq", names)

    def test_offline_fallback_generation(self):
        """Verify generation fallback when running without cloud keys."""
        resp = provider_manager.generate_with_fallback("Hello Jarvis, how are you?")
        self.assertIsNotNone(resp)
        self.assertIsInstance(resp.text, str)
        self.assertTrue(len(resp.text) > 0)



class TestAutomationManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])

    def test_crud_lifecycle(self):
        """Test full CRUD lifecycle of custom automations."""
        auto = self.mgr.create_automation(
            name="Test Time Check",
            action="check_time",
            parameters={},
            schedule_time=None
        )
        self.assertIsNotNone(auto)
        auto_id = auto['id']

        fetched = self.mgr.get_automation(auto_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched['name'], "Test Time Check")

        deleted = self.mgr.delete_automation(auto_id)
        self.assertTrue(deleted)


class TestVoice3System(unittest.TestCase):
    def test_hinglish_normalization(self):
        """Test translation and normalization of Hindi/Hinglish voice intents."""
        from FUNCTION.JARVIS_LISTEN.listen import normalize_hinglish, Trans_hindi_to_english, is_interruption_phrase
        self.assertEqual(normalize_hinglish("YouTube kholo"), "youtube open")
        self.assertEqual(normalize_hinglish("mujhe mausam batao"), "tell me the weather")
        self.assertEqual(normalize_hinglish("Python tutorials search karo"), "python tutorials search for")
        self.assertTrue(is_interruption_phrase("jarvis stop"))
        self.assertTrue(is_interruption_phrase("ruko"))
        self.assertTrue(is_interruption_phrase("chup"))


    def test_spoken_text_cleaner(self):
        """Test markdown and URL stripping for spoken voice output."""
        from VOICE.voice_engine import clean_spoken_text
        raw = "Here is the result: **Python 3.14** at https://python.org\n- Item 1\n- Item 2\n```print('hi')```"
        cleaned = clean_spoken_text(raw)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("```", cleaned)
        self.assertIn("Python 3.14", cleaned)


class TestSkillRegistry(unittest.TestCase):
    def test_skills_registration_and_listing(self):
        """Test skill registry discovers built-in domain skills."""
        from SKILLS.skill_registry import skill_registry
        skills = skill_registry.list(only_enabled=True)
        self.assertGreaterEqual(len(skills), 5)
        names = [s["name"] for s in skills]
        self.assertIn("system", names)
        self.assertIn("youtube", names)
        self.assertIn("browser", names)
        self.assertIn("weather", names)
        self.assertIn("automation", names)
        self.assertIn("memory", names)

    def test_skill_tools_and_capabilities(self):
        """Test skill tools aggregation and capability summary introspection."""
        from SKILLS.skill_registry import skill_registry
        tools = skill_registry.get_all_tools()
        self.assertIn("system.time", tools)
        self.assertIn("youtube.play", tools)
        self.assertIn("weather.get", tools)

        summary = skill_registry.get_capabilities_summary()
        self.assertIn("System", summary)
        self.assertIn("Youtube", summary)


class TestDynamicToolDiscovery(unittest.TestCase):
    def test_contextual_tool_selection(self):
        """Test contextual dynamic tool subset filtering based on prompt topic."""
        # 1. YouTube prompt
        yt_tools = tool_registry.get_contextual_tools(query="play some lofi music on youtube")
        yt_names = [t["name"] for t in yt_tools]
        self.assertTrue(any("youtube" in n for n in yt_names))
        self.assertFalse(any("automation.delete" in n for n in yt_names))

        # 2. Automation prompt
        auto_tools = tool_registry.get_contextual_tools(query="create morning alarm schedule automation")
        auto_names = [t["name"] for t in auto_tools]
        self.assertTrue(any("automation" in n for n in auto_names))
        self.assertFalse(any("youtube.play" in n for n in auto_names))

        # 3. Weather prompt
        w_tools = tool_registry.get_contextual_tools(query="how is the weather in Delhi")
        w_names = [t["name"] for t in w_tools]
        self.assertTrue(any("weather" in n for n in w_names))


if __name__ == "__main__":


    print("=" * 65)
    print("  RUNNING JARVIS AI FULL ADVANCED AGENT VERIFICATION SUITE")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

