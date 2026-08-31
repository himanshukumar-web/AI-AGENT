"""
JARVIS AI — OpenAI Provider Implementation
Integrates OpenAI GPT models (GPT-4o, GPT-4o-mini, etc.) with structured tool calling and streaming.
"""

import json
import os
from typing import Any, Dict, Generator, List, Optional
from BRAIN.LLM.base_provider import BaseLLMProvider, LLMResponse, ToolCall

try:
    from openai import OpenAI
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url
        super().__init__(model_name=model_name, **kwargs)
        self._client = None
        if self.api_key and HAS_OPENAI_SDK:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"

    def is_available(self) -> bool:
        return bool(self.api_key and HAS_OPENAI_SDK)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "available": self.is_available(),
            "has_sdk": HAS_OPENAI_SDK,
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
            if "type" in t and t["type"] == "function":
                formatted.append(t)
            else:
                formatted.append({
                    "type": "function",
                    "function": {
                        "name": t.get("name"),
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {"type": "object", "properties": {}}),
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
            raise RuntimeError("OpenAI provider is not configured or missing API key.")

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

        tool_calls_list: List[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                args = {}
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except Exception:
                    args = {}
                tool_calls_list.append(ToolCall(
                    name=tc.function.name,
                    arguments=args,
                    id=tc.id,
                ))

        usage_dict = {}
        if response.usage:
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            text=message.content or "",
            tool_calls=tool_calls_list,
            raw_response=response,
            model=self.model_name,
            provider=self.provider_name,
            usage=usage_dict,
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
            raise RuntimeError("OpenAI provider is not configured or missing API key.")

        messages = self._build_messages(prompt, system_prompt, history)
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
