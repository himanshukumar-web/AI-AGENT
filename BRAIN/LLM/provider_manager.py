"""
JARVIS AI — LLM Provider Manager & Dynamic Router
Manages provider lifecycle, automatic fallback chains, model routing, and error recovery.
"""

import os
from typing import Any, Dict, Generator, List, Optional
from colorama import Fore

from BRAIN.LLM.base_provider import BaseLLMProvider, LLMResponse, ToolCall
from BRAIN.LLM.openai_provider import OpenAIProvider
from BRAIN.LLM.gemini_provider import GeminiProvider
from BRAIN.LLM.ollama_provider import OllamaProvider
from BRAIN.LLM.groq_provider import GroqProvider


class FallbackOfflineProvider(BaseLLMProvider):
    """Fallback provider when no cloud API keys or local Ollama instances are available."""

    def __init__(self, **kwargs):
        super().__init__(model_name="rule-fallback", **kwargs)

    @property
    def provider_name(self) -> str:
        return "offline_fallback"

    @property
    def default_model(self) -> str:
        return "rule-fallback"

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "available": True,
            "note": "No active LLM backend detected. Using internal rule reasoning.",
        }

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResponse:
        return LLMResponse(
            text="I am currently running in offline rule mode without an active cloud LLM key.",
            model=self.model_name,
            provider=self.provider_name,
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> Generator[str, None, None]:
        yield "I am currently in offline rule mode."


class LLMProviderManager:
    """Manages LLM providers, dynamic routing, and fallback chains."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._active_provider: Optional[BaseLLMProvider] = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Register all supported LLM providers."""
        # 1. OpenAI
        try:
            self._providers["openai"] = OpenAIProvider()
        except Exception:
            pass

        # 2. Gemini
        try:
            self._providers["gemini"] = GeminiProvider()
        except Exception:
            pass

        # 3. Groq
        try:
            self._providers["groq"] = GroqProvider()
        except Exception:
            pass

        # 4. Ollama
        try:
            self._providers["ollama"] = OllamaProvider()
        except Exception:
            pass

        # 5. Offline Fallback
        self._providers["offline_fallback"] = FallbackOfflineProvider()

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Get provider by identifier."""
        return self._providers.get(name.lower().strip())

    def get_active_provider(self) -> BaseLLMProvider:
        """
        Determine and return the most appropriate active provider based on
        config, availability, and fallback hierarchy.
        """
        from config import LLM_PROVIDER, LLM_MODEL

        req_provider = (LLM_PROVIDER or "auto").lower().strip()

        # If user explicitly requested a specific provider
        if req_provider in self._providers and req_provider != "auto":
            prov = self._providers[req_provider]
            if prov.is_available():
                if LLM_MODEL:
                    prov.model_name = LLM_MODEL
                return prov
            print(Fore.YELLOW + f"  [LLM Warning] Configured provider '{req_provider}' is not available. Falling back...")

        # Auto detection hierarchy: OpenAI -> Gemini -> Groq -> Ollama -> Offline Fallback
        priority = ["openai", "gemini", "groq", "ollama"]
        for p_name in priority:
            p = self._providers.get(p_name)
            if p and p.is_available():
                if LLM_MODEL:
                    p.model_name = LLM_MODEL
                return p

        return self._providers["offline_fallback"]

    def list_available_providers(self) -> List[Dict[str, Any]]:
        """List all available providers and their metadata."""
        info = []
        for name, provider in self._providers.items():
            info.append(provider.get_model_info())
        return info

    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """
        Execute generation on active provider with automatic fallback if request fails.
        """
        primary = self.get_active_provider()
        candidates = [primary]

        # Add other available providers as fallbacks
        for p in self._providers.values():
            if p != primary and p.is_available():
                candidates.append(p)

        last_error = None
        for prov in candidates:
            try:
                resp = prov.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    history=history,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp
            except Exception as e:
                last_error = e
                print(Fore.YELLOW + f"  [LLM Failover] Provider '{prov.provider_name}' failed: {e}. Trying fallback...")
                continue

        # If all candidates failed, return offline fallback response
        return self._providers["offline_fallback"].generate(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            tools=tools,
        )


# Global singleton instance
provider_manager = LLMProviderManager()
