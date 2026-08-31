"""
JARVIS AI — Google Gemini Provider Implementation
Integrates Google Gemini models (gemini-2.0-flash, gemini-1.5-pro, etc.)
with structured tool calling, streaming, and direct HTTP/REST fallback.
"""

import json
import os
import requests
from typing import Any, Dict, Generator, List, Optional
from BRAIN.LLM.base_provider import BaseLLMProvider, LLMResponse, ToolCall


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider via standard REST interface."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, **kwargs):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        super().__init__(model_name=model_name, **kwargs)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "available": self.is_available(),
        }

    def _build_contents(self, prompt: str, history: Optional[List[Dict[str, str]]]) -> List[Dict[str, Any]]:
        contents = []
        if history:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        return contents

    def _format_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        declarations = []
        for t in tools:
            func = t.get("function", t)
            declarations.append({
                "name": func.get("name"),
                "description": func.get("description", ""),
                "parameters": func.get("parameters", {"type": "object", "properties": {}})
            })
        return [{"function_declarations": declarations}]

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
            raise RuntimeError("Gemini API key is not configured.")

        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": self._build_contents(prompt, history),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        formatted_tools = self._format_tools(tools)
        if formatted_tools:
            payload["tools"] = formatted_tools

        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return LLMResponse(text="", model=self.model_name, provider=self.provider_name)

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        text_parts = []
        tool_calls: List[ToolCall] = []

        for p in parts:
            if "text" in p:
                text_parts.append(p["text"])
            if "functionCall" in p:
                fc = p["functionCall"]
                tool_calls.append(ToolCall(
                    name=fc.get("name", ""),
                    arguments=fc.get("args", {}),
                    id=fc.get("name", "")
                ))

        usage_meta = data.get("usageMetadata", {})
        usage_dict = {
            "prompt_tokens": usage_meta.get("promptTokenCount", 0),
            "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
            "total_tokens": usage_meta.get("totalTokenCount", 0),
        }

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            raw_response=data,
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
        # For simplicity and reliability across proxies, use generate() and stream token words
        full_res = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if full_res.text:
            # Yield in word chunks to simulate natural streaming
            words = full_res.text.split(" ")
            for i, w in enumerate(words):
                yield w + (" " if i < len(words) - 1 else "")
