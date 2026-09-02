"""
JARVIS AI — Screen Analyzer & Visual Context Provider
Provides structured visual perception answering 'what's on my screen'
without authorizing direct actions.
"""

from typing import Any, Dict, List, Optional
from PIL import Image

from BRAIN.COMPUTER.screen.capture import screen_capture
from BRAIN.COMPUTER.window.window_manager import window_manager
from BRAIN.COMPUTER.vision.element_detector import ui_element_detector
from BRAIN.COMPUTER.vision.vision_provider import vision_provider_manager, VisionResponse


class ScreenAnalyzer:
    """Answers visual queries about the screen and active applications."""

    def __init__(self):
        pass

    def analyze_screen(
        self,
        query: str = "Describe what is currently visible on the screen",
        image: Optional[Image.Image] = None,
    ) -> Dict[str, Any]:
        """
        Analyze current screen or provided image.
        Returns structured description, active window context, and detected elements.
        """
        if image is None:
            image = screen_capture.capture_screen()

        # Gather OS window context
        active_window = window_manager.get_active_window()
        visible_windows = window_manager.list_windows()

        # Compress image
        b64 = screen_capture.get_base64_encoded(image, quality=80, max_dimension=1280)

        prompt = (
            f"User Question: '{query}'\n"
            f"Active Application: '{active_window.get('app_name')}' (Title: '{active_window.get('title')}').\n"
            "Provide a clear, concise visual description of what is displayed.\n"
            "Identify key UI components, open windows, and any visible content."
        )

        response: VisionResponse = vision_provider_manager.analyze_image_with_fallback(
            image_base64=b64,
            prompt=prompt,
        )

        # Detect prominent elements
        elements = ui_element_detector.detect_elements(image=image, query=query, min_confidence=0.50)

        return {
            "summary": response.raw_text,
            "active_window": active_window.get("title", "Unknown"),
            "active_app": active_window.get("app_name", "Unknown"),
            "visible_windows_count": len(visible_windows),
            "elements_count": len(elements),
            "elements": elements[:8],  # Top 8 elements for summary
            "provider": response.provider,
        }

    def what_is_on_screen(self) -> str:
        """User-friendly conversational answer to 'Jarvis, what's on my screen?'"""
        analysis = self.analyze_screen()
        app = analysis.get("active_app", "an application")
        win = analysis.get("active_window", "")
        summary = analysis.get("summary", "")

        msg = f"You are currently viewing {app}"
        if win and win != app:
            msg += f" with the window '{win}'"
        msg += f".\n{summary}"
        return msg.strip()

    def get_active_application_summary(self) -> Dict[str, Any]:
        """Returns concise application state summary."""
        active = window_manager.get_active_window()
        return {
            "app_name": active.get("app_name", "Unknown"),
            "title": active.get("title", "Unknown"),
            "is_maximized": active.get("is_maximized", False),
            "is_minimized": active.get("is_minimized", False),
            "bounds": active.get("bounds", [0, 0, 0, 0]),
        }


screen_analyzer = ScreenAnalyzer()
