"""
JARVIS AI — Vision Model Abstraction & Multi-Provider Layer
Provides configurable vision understanding (Gemini, OpenAI, Ollama, Offline Heuristic)
with image optimization and cost control.
"""

import base64
import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import requests

from config import (
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from BRAIN.UTILS.logger import jarvis_logger

DEFAULT_VISION_TIMEOUT = 15.0


class VisionResponse:
    def __init__(
        self,
        raw_text: str,
        elements: Optional[List[Dict[str, Any]]] = None,
        provider: str = "offline",
        model: str = "heuristic",
    ):
        self.raw_text = raw_text
        self.elements = elements or []
        self.provider = provider
        self.model = model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.raw_text,
            "elements": self.elements,
            "provider": self.provider,
            "model": self.model,
        }


class BaseVisionProvider(ABC):
    """Abstract interface for all Vision models."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str = "",
    ) -> VisionResponse:
        pass


class OfflineHeuristicVisionProvider(BaseVisionProvider):
    """
    Offline fallback when no external vision API is configured.
    Derives UI layout information from active window bounds and heuristic geometry.
    """

    @property
    def provider_name(self) -> str:
        return "offline_heuristic"

    def is_available(self) -> bool:
        return True

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str = "",
    ) -> VisionResponse:
        from BRAIN.COMPUTER.window.window_manager import window_manager
        active = window_manager.get_active_window()
        title = active.get("title", "Active Screen")
        app_name = active.get("app_name", "Application")
        bounds = active.get("bounds", [0, 0, 1920, 1080])

        elements: List[Dict[str, Any]] = []
        p_lower = prompt.lower()

        # Heuristic common UI elements based on active application
        bx, by, bw, bh = bounds
        if bw <= 0 or bh <= 0:
            bw, bh = 1920, 1080

        # Browser address bar / search box heuristics
        if any(b in app_name.lower() or b in title.lower() for b in ("chrome", "edge", "firefox", "browser")):
            elements.append({
                "element": "Address & Search Bar",
                "type": "text_input",
                "location": {"x": bx + int(bw * 0.5), "y": by + 82},
                "confidence": 0.88,
            })
            elements.append({
                "element": "New Tab Button",
                "type": "button",
                "location": {"x": bx + 280, "y": by + 20},
                "confidence": 0.85,
            })
            elements.append({
                "element": "Back Button",
                "type": "button",
                "location": {"x": bx + 25, "y": by + 82},
                "confidence": 0.85,
            })

        # Window control buttons (top right)
        elements.append({
            "element": "Close Button",
            "type": "button",
            "location": {"x": bx + bw - 25, "y": by + 15},
            "confidence": 0.95,
        })
        elements.append({
            "element": "Maximize Button",
            "type": "button",
            "location": {"x": bx + bw - 70, "y": by + 15},
            "confidence": 0.90,
        })
        elements.append({
            "element": "Minimize Button",
            "type": "button",
            "location": {"x": bx + bw - 115, "y": by + 15},
            "confidence": 0.90,
        })

        # Center content target
        elements.append({
            "element": "Main Window Workspace",
            "type": "workspace",
            "location": {"x": bx + int(bw * 0.5), "y": by + int(bh * 0.5)},
            "confidence": 0.80,
        })

        # Match specific element query if requested
        matched_text = f"Screen shows application '{app_name}' (Title: '{title}')."
        if "search" in p_lower:
            matched_text += " Detected search / address bar."
        elif "button" in p_lower:
            matched_text += " Detected standard window navigation buttons."

        return VisionResponse(
            raw_text=matched_text,
            elements=elements,
            provider=self.provider_name,
            model="heuristic-v1",
        )


class GeminiVisionProvider(BaseVisionProvider):
    """Google Gemini Vision Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or GEMINI_API_KEY
        self._model = "gemini-2.0-flash"

    @property
    def provider_name(self) -> str:
        return "gemini_vision"

    def is_available(self) -> bool:
        return bool(self._api_key and not self._api_key.startswith("your_"))

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str = "",
    ) -> VisionResponse:
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n{prompt}" if system_prompt else prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_VISION_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

        elements = self._extract_json_elements(text)
        return VisionResponse(raw_text=text, elements=elements, provider=self.provider_name, model=self._model)

    def _extract_json_elements(self, text: str) -> List[Dict[str, Any]]:
        try:
            match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return []


class OpenAIVisionProvider(BaseVisionProvider):
    """OpenAI GPT-4o / GPT-4o-mini Vision Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or OPENAI_API_KEY
        self._model = "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return "openai_vision"

    def is_available(self) -> bool:
        return bool(self._api_key and not self._api_key.startswith("your_"))

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str = "",
    ) -> VisionResponse:
        if not self.is_available():
            raise RuntimeError("OpenAI API key is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        })

        payload = {"model": self._model, "messages": messages, "temperature": 0.2, "max_tokens": 1024}

        resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_VISION_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        text = data["choices"][0]["message"]["content"]
        elements = self._extract_json_elements(text)
        return VisionResponse(raw_text=text, elements=elements, provider=self.provider_name, model=self._model)

    def _extract_json_elements(self, text: str) -> List[Dict[str, Any]]:
        try:
            match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return []


class OllamaVisionProvider(BaseVisionProvider):
    """Local Ollama Vision Provider (LLaVA / Moondream)."""

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self._model = "llava"

    @property
    def provider_name(self) -> str:
        return "ollama_vision"

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self._base_url}/api/tags", timeout=1.5)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                return any("llava" in m.lower() or "vision" in m.lower() for m in models)
        except Exception:
            pass
        return False

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str = "",
    ) -> VisionResponse:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": f"{system_prompt}\n{prompt}" if system_prompt else prompt,
            "images": [image_base64],
            "stream": False,
        }

        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        text = resp.json().get("response", "")
        return VisionResponse(raw_text=text, elements=[], provider=self.provider_name, model=self._model)


class VisionProviderManager:
    """Manages active vision providers and automatic fallback to offline heuristic."""

    def __init__(self):
        self._providers: Dict[str, BaseVisionProvider] = {
            "gemini": GeminiVisionProvider(),
            "openai": OpenAIVisionProvider(),
            "ollama": OllamaVisionProvider(),
            "offline": OfflineHeuristicVisionProvider(),
        }
        self._offline_fallback = OfflineHeuristicVisionProvider()

    def get_provider(self, name: Optional[str] = None) -> BaseVisionProvider:
        if name and name in self._providers:
            prov = self._providers[name]
            if prov.is_available():
                return prov

        # Default fallback chain: Gemini -> OpenAI -> Ollama -> Offline
        for p_name in ("gemini", "openai", "ollama"):
            p = self._providers[p_name]
            if p.is_available():
                return p

        return self._offline_fallback

    def analyze_image_with_fallback(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str = "",
        preferred_provider: Optional[str] = None,
    ) -> VisionResponse:
        """Attempts primary vision provider and automatically falls back to offline heuristic."""
        prov = self.get_provider(preferred_provider)
        try:
            return prov.analyze_image(image_base64, prompt, system_prompt)
        except Exception as e:
            jarvis_logger.warning("VISION", f"Vision provider '{prov.provider_name}' failed: {e}. Using offline fallback.")
            return self._offline_fallback.analyze_image(image_base64, prompt, system_prompt)


vision_provider_manager = VisionProviderManager()
