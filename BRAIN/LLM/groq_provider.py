"""
JARVIS AI — Groq Provider Implementation
High-speed inference for Llama models using the Groq API.
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional
from BRAIN.LLM.base_provider import BaseLLMProvider, LLMResponse, ToolCall

try:
    from groq import Groq
    HAS_GROQ_SDK = True
except ImportError:
    HAS_GROQ_SDK = False


class GroqProvider(BaseLLMProvider):
    """Groq API Provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        super().__init__(model_name=model_name, **kwargs)
        self._client = None
        if self.api_key and HAS_GROQ_SDK:
            self._client = Groq(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def default_model(self) -> str:
        return "llama-3.3-70b-versatile"

    def is_available(self) -> bool:
        return bool(self.api_key and HAS_GROQ_SDK)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "available": self.is_available(),
        }

    def _build_messages(self, prompt: str, system_prompt: str, history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for msg in history:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _format_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        formatted = []
        for t in tools:
            func = t.get("function", t)
            formatted.append({
                "type": "function",
                "function": {
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {"type": "object", "properties": {}}),
                }
            })
        return formatted

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("Groq provider is not configured or missing GROQ_API_KEY.")

        messages = self._build_messages(prompt, system_prompt, history)
        formatted_tools = self._format_tools(tools)

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if formatted_tools:
            kwargs["tools"] = formatted_tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        tool_calls: List[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                args = {}
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except Exception:
                    args = {}
                tool_calls.append(ToolCall(
                    name=tc.function.name,
                    arguments=args,
                    id=tc.id
                ))

        return LLMResponse(
            text=message.content or "",
            tool_calls=tool_calls,
            raw_response=response,
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
        if not self.is_available():
            raise RuntimeError("Groq provider is not configured.")

        messages = self._build_messages(prompt, system_prompt, history)
        stream = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
