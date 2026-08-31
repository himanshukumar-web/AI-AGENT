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


if __name__ == "__main__":
    print("=" * 65)
    print("  RUNNING JARVIS AI FULL ADVANCED AGENT VERIFICATION SUITE")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
