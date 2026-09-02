"""
JARVIS AI — Phase 5 Computer Vision & Controlled Computer Use Verification Suite
Comprehensive automated unit and integration tests for screen capture, monitor awareness,
controlled mouse/keyboard tools, window management, vision reasoning, safety gating,
action budgets, sensitive UI detection, emergency stop, and skill routing.
"""

import os
import sys
import unittest
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from BRAIN.COMPUTER.screen.monitor import monitor_manager, MonitorInfo
from BRAIN.COMPUTER.screen.capture import screen_capture
from BRAIN.COMPUTER.input.mouse import mouse_controller
from BRAIN.COMPUTER.input.keyboard import keyboard_controller
from BRAIN.COMPUTER.window.window_manager import window_manager
from BRAIN.COMPUTER.vision.vision_provider import vision_provider_manager, OfflineHeuristicVisionProvider
from BRAIN.COMPUTER.vision.element_detector import ui_element_detector
from BRAIN.COMPUTER.vision.screen_analyzer import screen_analyzer
from BRAIN.COMPUTER.safety.emergency_stop import emergency_stop_controller
from BRAIN.COMPUTER.safety.sensitive_detector import sensitive_detector
from BRAIN.COMPUTER.safety.computer_safety import computer_safety_manager, ComputerRiskLevel
from BRAIN.COMPUTER.visual_agent import visual_action_agent
from BRAIN.TOOLS.tool_registry import tool_registry
from BRAIN.TOOLS.safety_manager import safety_manager, RiskLevel
from SKILLS.skill_registry import skill_registry
from BRAIN.CORE_AGENT.router import intelligent_router, RouteCategory


class TestScreenAndMonitor(unittest.TestCase):
    """Test screen topology, dimensions, coordinates bounds, and capture abstractions."""

    def test_screen_dimensions(self):
        width, height = monitor_manager.get_screen_dimensions()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_monitor_bounds_validation(self):
        w, h = monitor_manager.get_screen_dimensions()
        # Valid points
        self.assertTrue(monitor_manager.is_point_within_bounds(0, 0))
        self.assertTrue(monitor_manager.is_point_within_bounds(w // 2, h // 2))
        # Invalid points
        self.assertFalse(monitor_manager.is_point_within_bounds(-50, 100))
        self.assertFalse(monitor_manager.is_point_within_bounds(w + 1000, h + 1000))

    def test_screen_capture(self):
        img = screen_capture.capture_screen()
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.size[0], 0)
        self.assertGreater(img.size[1], 0)

        # Base64 encoding with compression
        b64 = screen_capture.get_base64_encoded(img, max_dimension=800, quality=70)
        self.assertIsInstance(b64, str)
        self.assertGreater(len(b64), 100)

    def test_active_window_capture(self):
        img, title = screen_capture.capture_active_window()
        self.assertIsNotNone(img)
        self.assertIsInstance(title, str)


class TestMouseAndKeyboardControl(unittest.TestCase):
    """Test boundary checks, failsafes, and input restrictions."""

    def test_mouse_coordinate_validation(self):
        w, h = monitor_manager.get_screen_dimensions()
        valid, _ = mouse_controller.validate_coordinates(w // 2, h // 2)
        self.assertTrue(valid)

        invalid_neg, err1 = mouse_controller.validate_coordinates(-10, 50)
        self.assertFalse(invalid_neg)
        self.assertIn("outside active screen bounds", err1)

        invalid_out, err2 = mouse_controller.validate_coordinates(w + 500, h + 500)
        self.assertFalse(invalid_out)
        self.assertIn("outside active screen bounds", err2)

    def test_mouse_position_query(self):
        pos = mouse_controller.get_position()
        self.assertIsInstance(pos, tuple)
        self.assertEqual(len(pos), 2)
        self.assertIsInstance(pos[0], int)
        self.assertIsInstance(pos[1], int)

    def test_keyboard_key_whitelisting(self):
        # Valid key syntax validation
        res_ok = keyboard_controller.press_key("enter", presses=1)
        self.assertTrue(res_ok.get("success"))

        # Invalid key rejection
        res_bad = keyboard_controller.press_key("nonexistent_dangerous_key")
        self.assertFalse(res_bad.get("success"))
        self.assertIn("whitelist", res_bad.get("error", "").lower())

    def test_hotkey_whitelisting(self):
        # Safe hotkey validation
        res_safe = keyboard_controller.hotkey("ctrl", "c")
        self.assertTrue(res_safe.get("success"))

        # Unsafe hotkey rejection
        res_unsafe = keyboard_controller.hotkey("ctrl", "alt", "del")
        self.assertFalse(res_unsafe.get("success"))
        self.assertIn("restricted", res_unsafe.get("error", "").lower())


class TestWindowManager(unittest.TestCase):
    """Test window introspection, application context, and focus management."""

    def test_get_active_window(self):
        win = window_manager.get_active_window()
        self.assertIn("title", win)
        self.assertIn("bounds", win)
        self.assertIn("app_name", win)
        self.assertIsInstance(win["bounds"], list)
        self.assertEqual(len(win["bounds"]), 4)

    def test_list_windows(self):
        windows = window_manager.list_windows()
        self.assertIsInstance(windows, list)
        if windows:
            first = windows[0]
            self.assertIn("hwnd", first)
            self.assertIn("title", first)

    def test_find_window_substring(self):
        windows = window_manager.list_windows()
        if windows:
            sample_title = windows[0]["title"]
            found = window_manager.find_window(sample_title[:6])
            self.assertIsNotNone(found)


class TestVisionAndElementDetection(unittest.TestCase):
    """Test vision provider abstraction, element discovery, and structured grounding."""

    def test_offline_heuristic_provider(self):
        prov = OfflineHeuristicVisionProvider()
        self.assertTrue(prov.is_available())
        resp = prov.analyze_image("dummy_b64", "Find the close button")
        self.assertIsNotNone(resp.raw_text)
        self.assertIsInstance(resp.elements, list)
        self.assertEqual(resp.provider, "offline_heuristic")

    def test_element_detection_confidence(self):
        elements = ui_element_detector.detect_elements(query="button", min_confidence=0.50)
        self.assertIsInstance(elements, list)
        for el in elements:
            self.assertIn("element", el)
            self.assertIn("location", el)
            self.assertIn("confidence", el)
            self.assertGreaterEqual(el["confidence"], 0.50)

    def test_find_best_element(self):
        best, msg = ui_element_detector.find_best_element("close button", min_confidence=0.50)
        self.assertIsNotNone(best)
        self.assertIn("Close", best["element"])
        self.assertIn("x", best["location"])
        self.assertIn("y", best["location"])

    def test_screen_analyzer(self):
        res = screen_analyzer.analyze_screen()
        self.assertIn("summary", res)
        self.assertIn("active_window", res)
        self.assertIn("active_app", res)

        text_ans = screen_analyzer.what_is_on_screen()
        self.assertIsInstance(text_ans, str)
        self.assertGreater(len(text_ans), 10)


class TestSafetySensitiveUIAndEmergencyStop(unittest.TestCase):
    """Test safety tiers, credentials redaction, budget caps, and emergency stop."""

    def setUp(self):
        emergency_stop_controller.reset()
        computer_safety_manager.end_task()

    def tearDown(self):
        emergency_stop_controller.reset()
        computer_safety_manager.end_task()

    def test_emergency_stop_trigger_and_abort(self):
        self.assertFalse(emergency_stop_controller.is_stopped())
        emergency_stop_controller.request_stop("Testing emergency stop")
        self.assertTrue(emergency_stop_controller.is_stopped())

        # Pre-action check must block actions when stopped
        safe, err = computer_safety_manager.check_pre_action_safety("computer.click")
        self.assertFalse(safe)
        self.assertIn("Emergency stop is active", err)

        emergency_stop_controller.reset()
        self.assertFalse(emergency_stop_controller.is_stopped())

    def test_emergency_stop_phrases(self):
        self.assertTrue(emergency_stop_controller.is_emergency_phrase("jarvis stop"))
        self.assertTrue(emergency_stop_controller.is_emergency_phrase("stop everything"))
        self.assertTrue(emergency_stop_controller.is_emergency_phrase("cancel computer task"))
        self.assertTrue(emergency_stop_controller.is_emergency_phrase("ruko"))
        self.assertFalse(emergency_stop_controller.is_emergency_phrase("click the search box"))

    def test_sensitive_ui_detection(self):
        is_sens, _ = sensitive_detector.is_sensitive_text("Please enter your password below")
        self.assertTrue(is_sens)

        is_sens_card, _ = sensitive_detector.is_sensitive_text("credit card number: 4111 2222 3333 4444")
        self.assertTrue(is_sens_card)

        is_safe, _ = sensitive_detector.is_sensitive_text("Search for machine learning tutorials")
        self.assertFalse(is_safe)

    def test_secret_redaction(self):
        text = "My OpenAI key is sk-abcdef1234567890abcdef12345678 and pin is 1234"
        redacted = sensitive_detector.redact_sensitive_text(text)
        self.assertNotIn("sk-abcdef", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_risk_level_classification(self):
        self.assertEqual(computer_safety_manager.classify_action("computer.screenshot"), ComputerRiskLevel.LOW)
        self.assertEqual(computer_safety_manager.classify_action("computer.get_screen_size"), ComputerRiskLevel.LOW)
        self.assertEqual(computer_safety_manager.classify_action("computer.scroll"), ComputerRiskLevel.LOW)
        self.assertEqual(computer_safety_manager.classify_action("computer.click"), ComputerRiskLevel.MEDIUM)
        self.assertEqual(computer_safety_manager.classify_action("computer.type"), ComputerRiskLevel.MEDIUM)
        self.assertEqual(computer_safety_manager.classify_action("computer.click", {"element": "Submit Form"}), ComputerRiskLevel.HIGH)
        self.assertEqual(computer_safety_manager.classify_action("computer.close_window"), ComputerRiskLevel.HIGH)

    def test_action_budget_limit(self):
        computer_safety_manager.start_task("budget_test")
        computer_safety_manager.max_actions = 3

        self.assertTrue(computer_safety_manager.check_pre_action_safety("computer.scroll")[0])
        self.assertTrue(computer_safety_manager.check_pre_action_safety("computer.scroll")[0])
        self.assertTrue(computer_safety_manager.check_pre_action_safety("computer.scroll")[0])

        # 4th action exceeds budget of 3
        ok4, err4 = computer_safety_manager.check_pre_action_safety("computer.scroll")
        self.assertFalse(ok4)
        self.assertIn("Action limit reached", err4)
        computer_safety_manager.end_task()


class TestVisualActionLoopAndToolRegistry(unittest.TestCase):
    """Test namespaced tools registration, aliases, and visual execution."""

    def setUp(self):
        emergency_stop_controller.reset()
        computer_safety_manager.end_task()

    def tearDown(self):
        emergency_stop_controller.reset()
        computer_safety_manager.end_task()

    def test_canonical_and_aliased_tools(self):
        self.assertEqual(tool_registry.resolve_tool_name("screenshot"), "computer.screenshot")
        self.assertEqual(tool_registry.resolve_tool_name("get_screen_size"), "computer.get_screen_size")
        self.assertEqual(tool_registry.resolve_tool_name("click"), "computer.click")
        self.assertEqual(tool_registry.resolve_tool_name("type_text"), "computer.type")
        self.assertEqual(tool_registry.resolve_tool_name("scroll"), "computer.scroll")
        self.assertEqual(tool_registry.resolve_tool_name("active_window"), "computer.get_active_window")
        self.assertEqual(tool_registry.resolve_tool_name("emergency_stop"), "computer.emergency_stop")

    def test_contextual_computer_tool_filtering(self):
        tools = tool_registry.get_contextual_tools("click the submit button on screen")
        names = [t["name"] for t in tools]
        self.assertIn("computer.click", names)
        self.assertIn("computer.screenshot", names)
        self.assertIn("computer.find_element", names)

    def test_execute_safe_computer_tools(self):
        res_size = tool_registry.execute_tool("computer.get_screen_size")
        self.assertTrue(res_size.get("success"))
        self.assertIn("width", res_size.get("data", {}))

        res_win = tool_registry.execute_tool("computer.get_active_window")
        self.assertTrue(res_win.get("success"))
        self.assertIn("title", res_win.get("data", {}))

    def test_visual_action_verification(self):
        res = visual_action_agent.execute_single_action("scroll", arguments={"clicks": 0})
        self.assertTrue(res.get("success"), f"Action failed with: {res}")
        self.assertTrue(res.get("verified"))


class TestComputerSkillAndNaturalRouting(unittest.TestCase):
    """Test modular skill registration and intelligent intent routing."""

    def test_skill_registered(self):
        skill = skill_registry.get("computer")
        self.assertIsNotNone(skill)
        self.assertTrue(skill.enabled)
        tools = skill.get_tools()
        self.assertIn("computer.screenshot", tools)
        self.assertIn("computer.click", tools)
        self.assertIn("computer.emergency_stop", tools)

        caps = skill.get_capabilities_list()
        self.assertGreaterEqual(len(caps), 4)

    def test_routing_computer_intents(self):
        cat_screen, _ = intelligent_router.route("what's on my screen")
        self.assertEqual(cat_screen, RouteCategory.SIMPLE_COMMAND)

        cat_app, _ = intelligent_router.route("what application is open")
        self.assertEqual(cat_app, RouteCategory.SIMPLE_COMMAND)

        cat_scroll, _ = intelligent_router.route("scroll down")
        self.assertEqual(cat_scroll, RouteCategory.SIMPLE_COMMAND)

        cat_stop, meta_stop = intelligent_router.route("jarvis stop")
        self.assertEqual(cat_stop, RouteCategory.INTERRUPT)
        self.assertEqual(meta_stop.get("action"), "stop")


if __name__ == "__main__":
    unittest.main(verbosity=2)
