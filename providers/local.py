"""
Arkadia Knowledge OS — Local LLM Provider Adapter (Ollama)
===========================================================
Implements BaseProvider for any Ollama-served model.
Satisfies LAW II: Local First. Operates fully offline.
Business logic lives in Oracle/Kernel, NOT here.
"""

import os
import time
import json
from typing import AsyncIterator, Optional

import httpx

from providers.base import BaseProvider, ProviderMessage, ProviderResponse

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


class LocalLLMProvider(BaseProvider):
    name = "local"
    display_name = "Local LLM (Ollama)"

    def __init__(self, model: str = "llama3"):
        self.model = os.environ.get("LOCAL_LLM_MODEL", model)

    def _ollama_running(self) -> bool:
        try:
            r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def authenticate(self) -> bool:
        return self._ollama_running()

    def send(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> ProviderResponse:
        if not self._ollama_running():
            raise RuntimeError(f"Ollama not running at {OLLAMA_BASE}")

        # Build prompt — Ollama /api/chat supports the messages format
        payload: dict = {
            "model": self.model,
            "messages": [],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload["messages"].append({"role": msg.role, "content": msg.content})

        t0 = time.time()
        r = httpx.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=120.0)
        r.raise_for_status()
        latency_ms = int((time.time() - t0) * 1000)

        data = r.json()
        content = data.get("message", {}).get("content", "")
        return ProviderResponse(
            content=content,
            model=self.model,
            provider_name=self.name,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            raw={"latency_ms": latency_ms, "total_duration_ns": data.get("total_duration")},
        )

    async def stream(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        payload: dict = {
            "model": self.model,
            "messages": [],
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload["messages"].append({"role": msg.role, "content": msg.content})

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE}/api/chat", json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            text = chunk.get("message", {}).get("content", "")
                            if text:
                                yield text
                        except json.JSONDecodeError:
                            continue

    def models(self) -> list[str]:
        try:
            r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=3.0)
            data = r.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return [self.model]

    def capabilities(self) -> list[str]:
        return ["chat", "stream"]

    def health(self) -> dict:
        if not self._ollama_running():
            return {
                "status": "unconfigured",
                "model": self.model,
                "latency_ms": 0,
                "reason": f"Ollama not running at {OLLAMA_BASE}. Install Ollama and run: ollama pull {self.model}",
            }
        available = self.models()
        if self.model not in available:
            return {
                "status": "unconfigured",
                "model": self.model,
                "latency_ms": 0,
                "reason": f"Model '{self.model}' not pulled. Run: ollama pull {self.model}",
            }
        return {"status": "ok", "model": self.model, "latency_ms": 0, "available_models": available}
