"""
JARVIS AI — Base LLM Provider Abstraction
Unified interface for all supported Large Language Model backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional


@dataclass
class ToolCall:
    """Represents a structured tool execution request from the model."""
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None


@dataclass
class LLMResponse:
    """Unified response container returned by all LLM providers."""
    text: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_response: Any = None
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM providers."""

    def __init__(self, model_name: Optional[str] = None, **kwargs):
        self.model_name = model_name or self.default_model
        self.extra_config = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'openai', 'gemini', 'ollama', 'groq')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier for this provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available (e.g. valid API key or reachable server)."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the current model and provider."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """Generate a complete response from the LLM."""
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> Generator[str, None, None]:
        """Stream response tokens from the LLM as they become available."""
        pass
