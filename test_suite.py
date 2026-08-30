"""
JARVIS AI — Comprehensive Verification & Test Suite
Tests all core subsystems under Python 3.14.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import PATHS, import_module_from_path, USER_NAME, ASSISTANT_NAME


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


class TestJarvisBrain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain_mod = import_module_from_path('brain1', PATHS['brain1'])

    def test_command_normalizer(self):
        """Test natural language prefix and wake word stripping."""
        norm = self.brain_mod.normalize_command
        self.assertEqual(norm("Jarvis open youtube"), "open youtube")
        self.assertEqual(norm("please open notepad for me"), "open notepad")
        self.assertEqual(norm("can you please tell me a joke"), "tell me a joke")
        self.assertEqual(norm("could you check the weather right now"), "check the weather")

    def test_greetings(self):
        """Test standard greetings."""
        res = self.brain_mod.brain_cmd("hello jarvis")
        self.assertIsNotNone(res)
        self.assertIsInstance(res, str)

    def test_joke_utility(self):
        """Test joke command."""
        res = self.brain_mod.brain_cmd("tell me a joke")
        self.assertIsNotNone(res)
        self.assertTrue(len(res) > 5)

    def test_advice_utility(self):
        """Test advice command."""
        res = self.brain_mod.brain_cmd("give me advice")
        self.assertIsNotNone(res)
        self.assertTrue("advice" in res.lower())

    def test_qna_match(self):
        """Test exact QNA dataset retrieval."""
        res = self.brain_mod.brain_cmd("who created you")
        self.assertIsNotNone(res)


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
        # May return None if under threshold, or string answer
        if res is not None:
            self.assertIsInstance(res, str)


class TestAutomationManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mgr = import_module_from_path('automation_manager', PATHS['automation_manager'])

    def test_crud_lifecycle(self):
        """Test full CRUD lifecycle of custom automations."""
        # 1. Create
        auto = self.mgr.create_automation(
            name="Test Time Check",
            action="check_time",
            parameters={},
            schedule_time=None
        )
        self.assertIsNotNone(auto)
        auto_id = auto['id']

        # 2. Read / Get
        fetched = self.mgr.get_automation(auto_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched['name'], "Test Time Check")
        self.assertTrue(fetched['enabled'])

        # 3. Edit / Update
        updated = self.mgr.edit_automation(auto_id, name="Renamed Time Check")
        self.assertIsNotNone(updated)
        self.assertEqual(updated['name'], "Renamed Time Check")

        # 4. Disable / Enable
        disabled = self.mgr.disable_automation(auto_id)
        self.assertFalse(disabled['enabled'])

        enabled = self.mgr.enable_automation(auto_id)
        self.assertTrue(enabled['enabled'])

        # 5. Execute
        success = self.mgr.execute_automation(auto_id)
        self.assertTrue(success)

        # 6. Check History
        history = self.mgr.get_automation_history(speak_output=False)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[-1]['automation_id'], auto_id)
        self.assertEqual(history[-1]['status'], 'success')

        # 7. Delete
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


class TestSubsystemIntegrations(unittest.TestCase):
    def test_automation_dispatcher(self):
        """Test master automation dispatcher keywords."""
        auto_int = import_module_from_path('automation_intregation', PATHS['automation_integration'])
        # Listing automations should be recognized
        handled = auto_int.process_automation("list automations")
        self.assertTrue(handled)


if __name__ == "__main__":
    print("=" * 60)
    print("  RUNNING JARVIS AI FULL VERIFICATION TEST SUITE (Python 3.14)")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
