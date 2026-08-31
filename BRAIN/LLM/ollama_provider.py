"""
JARVIS AI — Ollama Local Provider Implementation
Supports fully offline, local inference via Ollama (Llama 3, Mistral, Qwen, DeepSeek, etc.).
"""

import json
import os
import requests
from typing import Any, Dict, Generator, List, Optional
from BRAIN.LLM.base_provider import BaseLLMProvider, LLMResponse, ToolCall


class OllamaProvider(BaseLLMProvider):
    """Ollama Local LLM Provider."""

    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None, **kwargs):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        super().__init__(model_name=model_name or os.environ.get("OLLAMA_MODEL", "llama3:latest"), **kwargs)

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return "llama3:latest"

    def is_available(self) -> bool:
        """Check if local Ollama server is running."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "base_url": self.base_url,
            "available": self.is_available(),
            "offline": True,
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
            raise RuntimeError(f"Ollama server is not reachable at {self.base_url}. Please ensure 'ollama serve' is running.")

        url = f"{self.base_url}/api/chat"
        messages = self._build_messages(prompt, system_prompt, history)
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        formatted_tools = self._format_tools(tools)
        if formatted_tools:
            payload["tools"] = formatted_tools

        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Ollama error ({resp.status_code}): {resp.text}")

        data = resp.json()
        message = data.get("message", {})
        content = message.get("content", "")
        raw_tools = message.get("tool_calls", [])

        tool_calls: List[ToolCall] = []
        for rt in raw_tools:
            func = rt.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            tool_calls.append(ToolCall(
                name=func.get("name", ""),
                arguments=args if isinstance(args, dict) else {},
                id=func.get("name", "")
            ))

        return LLMResponse(
            text=content,
            tool_calls=tool_calls,
            raw_response=data,
            model=self.model_name,
            provider=self.provider_name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            }
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
            raise RuntimeError(f"Ollama server is not reachable at {self.base_url}")

        url = f"{self.base_url}/api/chat"
        messages = self._build_messages(prompt, system_prompt, history)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        resp = requests.post(url, json=payload, stream=True, timeout=60)
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
