"""
JARVIS AI — Comprehensive Verification & Modern Agent Test Suite
Tests all core subsystems, LLM providers, tools, memory, safety, and voice under Python 3.14.
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
from BRAIN.MEMORY.memory_manager import MemoryManager
from BRAIN.MEMORY.conversation_manager import conversation_manager
from BRAIN.PROMPTS.system_prompt import get_system_prompt
from VOICE.voice_engine import voice_engine


class TestJarvisConfig(unittest.TestCase):
    def test_paths_exist(self):
        """Verify all critical files exist in declared paths."""
        for name, path in PATHS.items():
            if name in ['automations_db', 'automation_logs', 'memory_manager', 'safety_manager']:
                if name in ['automations_db', 'automation_logs']:
                    continue  # Runtime files created on demand
            self.assertTrue(os.path.exists(path), f"Path does not exist: {path}")

    def test_config_variables(self):
        """Verify configuration constants."""
        self.assertIsInstance(USER_NAME, str)
        self.assertIsInstance(ASSISTANT_NAME, str)
        self.assertIsInstance(LLM_PROVIDER, str)


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

    def test_active_provider_fallback(self):
        """Ensure an active provider is always resolvable without crashing."""
        active = provider_manager.get_active_provider()
        self.assertIsNotNone(active)
        self.assertIsInstance(active, BaseLLMProvider)

    def test_offline_fallback_generation(self):
        """Verify offline fallback provider generates structured responses."""
        fallback = provider_manager.get_provider("offline_fallback")
        self.assertIsNotNone(fallback)
        resp = fallback.generate("Hello")
        self.assertIsInstance(resp, LLMResponse)
        self.assertTrue(len(resp.text) > 0)


class TestToolRegistry(unittest.TestCase):
    def test_tool_definitions_schema(self):
        """Verify tool schemas are valid and properly structured."""
        definitions = tool_registry.get_tool_definitions()
        self.assertTrue(len(definitions) >= 10)
        tool_names = [d["name"] for d in definitions]
        self.assertIn("get_time", tool_names)
        self.assertIn("get_weather", tool_names)
        self.assertIn("get_battery_status", tool_names)
        self.assertIn("create_automation", tool_names)
        self.assertIn("list_automations", tool_names)

    def test_time_tool_execution(self):
        """Test get_time tool returns structured output."""
        res = tool_registry.execute_tool("get_time")
        self.assertTrue(res["success"])
        self.assertIn("time", res["data"])
        self.assertIn("formatted", res["data"])

    def test_battery_tool_execution(self):
        """Test get_battery_status tool returns structured output."""
        res = tool_registry.execute_tool("get_battery_status")
        self.assertTrue(res["success"])
        self.assertIn("percent", res["data"])

    def test_unregistered_tool_rejection(self):
        """Test unregistered/arbitrary tool execution is blocked."""
        res = tool_registry.execute_tool("arbitrary_exec_bash")
        self.assertFalse(res["success"])
        self.assertIn("not registered", res["error"])


class TestSafetyManager(unittest.TestCase):
    def test_risk_levels(self):
        """Verify risk levels are correctly categorized."""
        self.assertEqual(safety_manager.get_risk_level("get_time"), RiskLevel.LOW)
        self.assertEqual(safety_manager.get_risk_level("youtube_play"), RiskLevel.MEDIUM)
        self.assertEqual(safety_manager.get_risk_level("delete_automation"), RiskLevel.HIGH)

    def test_safety_block_unknown_action(self):
        """Verify unauthorized actions fail validation."""
        allowed = safety_manager.validate_execution("dangerous_shell_tool", {})
        self.assertFalse(allowed)


class TestMemoryManager(unittest.TestCase):
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

    def test_fact_storage_and_recall(self):
        """Test storing, updating, recalling, and deleting long-term facts."""
        # 1. Store
        ok = self.mem.store_fact("favorite_genre", "synthwave", category="preference")
        self.assertTrue(ok)

        # 2. Get
        val = self.mem.get_fact("favorite_genre")
        self.assertEqual(val, "synthwave")

        # 3. Recall with query
        recalled = self.mem.recall_facts(query="synthwave")
        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["key"], "favorite_genre")

        # 4. Update
        self.mem.store_fact("favorite_genre", "ambient lofi")
        self.assertEqual(self.mem.get_fact("favorite_genre"), "ambient lofi")

        # 5. Delete
        deleted = self.mem.delete_fact("favorite_genre")
        self.assertTrue(deleted)
        self.assertIsNone(self.mem.get_fact("favorite_genre"))

    def test_conversation_logging(self):
        """Test conversation turn logging and retrieval."""
        session_id = "test_session_1"
        self.mem.log_turn(session_id, "user", "What is my schedule?")
        self.mem.log_turn(session_id, "assistant", "You have no scheduled events.")

        history = self.mem.get_recent_history(session_id, limit=5)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")


class TestConversationManager(unittest.TestCase):
    def test_context_management(self):
        """Test multi-turn state, follow-up hints, and sliding context."""
        conversation_manager.reset()
        conversation_manager.add_user_message("Open YouTube")
        conversation_manager.set_context_state(active_topic="youtube", last_action="open_website")
        conversation_manager.add_assistant_message("Opening YouTube, sir.")

        state = conversation_manager.get_context_state()
        self.assertEqual(state["active_topic"], "youtube")

        hint = conversation_manager.resolve_follow_up_hint("search for Arijit Singh")
        self.assertIsNotNone(hint)
        self.assertIn("YouTube", hint)


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

    def test_system_prompt_builder(self):
        """Test system prompt formatting."""
        prompt = get_system_prompt(custom_facts="- favorite_artist: Hans Zimmer")
        self.assertIn(ASSISTANT_NAME, prompt)
        self.assertIn("Hans Zimmer", prompt)


class TestVoiceEngine(unittest.TestCase):
    def test_voice_engine_properties(self):
        """Verify voice engine attributes and methods."""
        self.assertFalse(voice_engine.is_speaking)
        voice_engine.stop_speaking()
        self.assertFalse(voice_engine.is_speaking)


class TestMachineLearning(unittest.TestCase):
    def test_modal_2_classifier(self):
        """Test Naive Bayes Intent Classifier."""
        modal2 = import_module_from_path('modal_2', PATHS['modal_2'])
        res = modal2.get_response("hello")
        self.assertIsNotNone(res)
        self.assertIsInstance(res, str)

    def test_modal_1_tfidf(self):
        """Test TF-IDF QA engine."""
        modal1 = import_module_from_path('modal_1', PATHS['modal_1'])
        res = modal1.mind("who are you")
        if res is not None:
            self.assertIsInstance(res, str)


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

        updated = self.mgr.edit_automation(auto_id, name="Renamed Time Check")
        self.assertIsNotNone(updated)
        self.assertEqual(updated['name'], "Renamed Time Check")

        deleted = self.mgr.delete_automation(auto_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.mgr.get_automation(auto_id))

    def test_security_allowlist(self):
        """Test that invalid/unauthorized actions are strictly rejected."""
        bad_auto = self.mgr.create_automation(
            name="Malicious Command",
            action="rm_rf_system",
            parameters={"cmd": "calc.exe"}
        )
        self.assertIsNone(bad_auto)


if __name__ == "__main__":
    print("=" * 65)
    print("  RUNNING JARVIS AI FULL MODERN AGENT VERIFICATION SUITE")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
