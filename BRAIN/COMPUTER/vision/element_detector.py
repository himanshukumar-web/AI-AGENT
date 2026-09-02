"""
JARVIS AI — UI Element Detection & Structured Grounding
Detects buttons, text fields, links, dialogs, and tabs with confidence scoring
and coordinate bounds validation.
"""

from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from BRAIN.COMPUTER.screen.capture import screen_capture
from BRAIN.COMPUTER.screen.monitor import monitor_manager
from BRAIN.COMPUTER.vision.vision_provider import vision_provider_manager, VisionResponse

DEFAULT_CONFIDENCE_THRESHOLD = 0.60


class UIElementDetector:
    """Detects and localizes interactive UI elements on the current display."""

    def __init__(self, default_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        self._default_threshold = default_threshold

    def detect_elements(
        self,
        image: Optional[Image.Image] = None,
        query: str = "",
        min_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect UI elements from an image or current live screen capture.
        Returns a list of structured element dictionaries.
        """
        threshold = min_confidence if min_confidence is not None else self._default_threshold

        if image is None:
            image = screen_capture.capture_screen()

        b64 = screen_capture.get_base64_encoded(image, quality=80, max_dimension=1280)

        prompt = (
            f"Analyze the screen and locate the UI element: '{query}'.\n"
            "Identify interactive elements (buttons, inputs, links, tabs, dialogs).\n"
            "Return JSON array of elements with exact pixel coordinates:\n"
            "[{\"element\": \"Element name\", \"type\": \"button|text_input|link|tab\", "
            "\"location\": {\"x\": 500, \"y\": 300}, \"confidence\": 0.95}]"
        )

        response: VisionResponse = vision_provider_manager.analyze_image_with_fallback(
            image_base64=b64,
            prompt=prompt,
        )

        elements: List[Dict[str, Any]] = []
        screen_w, screen_h = monitor_manager.get_screen_dimensions()

        for el in response.elements:
            loc = el.get("location", {})
            x = loc.get("x", 0)
            y = loc.get("y", 0)
            conf = float(el.get("confidence", 0.0))

            # Validate coordinate bounds
            if 0 <= x <= screen_w and 0 <= y <= screen_h and conf >= threshold:
                elements.append({
                    "element": el.get("element", "UI Element"),
                    "type": el.get("type", "unknown"),
                    "location": {"x": int(x), "y": int(y)},
                    "confidence": round(conf, 2),
                    "provider": response.provider,
                })

        return elements

    def find_best_element(
        self,
        target_description: str,
        image: Optional[Image.Image] = None,
        min_confidence: Optional[float] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Locate the single best match for a given element description.
        Enforces confidence threshold.
        """
        threshold = min_confidence if min_confidence is not None else self._default_threshold
        elements = self.detect_elements(image=image, query=target_description, min_confidence=threshold)

        if not elements:
            return None, f"No UI element matching '{target_description}' detected with confidence >= {threshold:.0%}."

        # Rank by match score and confidence
        target_lower = target_description.lower()
        best_match = None
        best_score = -1.0

        for el in elements:
            name_lower = el["element"].lower()
            type_lower = el["type"].lower()
            conf = el["confidence"]

            # Relevance boost
            score = conf
            if target_lower in name_lower or name_lower in target_lower:
                score += 1.0
            if "button" in target_lower and type_lower == "button":
                score += 0.5
            if ("search" in target_lower or "input" in target_lower) and type_lower == "text_input":
                score += 0.5

            if score > best_score:
                best_score = score
                best_match = el

        if best_match and best_match["confidence"] >= threshold:
            return best_match, "Element located successfully."

        return None, f"Match confidence too low for '{target_description}'."


ui_element_detector = UIElementDetector()
