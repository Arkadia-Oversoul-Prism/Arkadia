"""
Arkadia Knowledge OS — OpenAI GPT Provider Adapter
====================================================
Implements BaseProvider for OpenAI GPT via the official openai SDK.
Business logic lives in Oracle/Kernel, NOT here.
"""

import os
import time
from typing import AsyncIterator, Optional

from providers.base import BaseProvider, ProviderMessage, ProviderResponse


class GPTProvider(BaseProvider):
    name = "gpt"
    display_name = "OpenAI GPT"

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def _get_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY", "") or None

    def _get_client(self):
        from openai import OpenAI
        key = self._get_key()
        if not key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        return OpenAI(api_key=key)

    def authenticate(self) -> bool:
        return bool(self._get_key())

    def send(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> ProviderResponse:
        client = self._get_client()

        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

        t0 = time.time()
        response = client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.time() - t0) * 1000)

        content = response.choices[0].message.content or ""
        usage = response.usage
        return ProviderResponse(
            content=content,
            model=self.model,
            provider_name=self.name,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            raw={"latency_ms": latency_ms, "finish_reason": response.choices[0].finish_reason},
        )

    async def stream(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

        stream = client.chat.completions.create(
            model=self.model, messages=openai_messages,
            temperature=temperature, stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

    def capabilities(self) -> list[str]:
        return ["chat", "stream", "vision", "function_call"]

    def health(self) -> dict:
        if not self.authenticate():
            return {"status": "unconfigured", "model": self.model, "latency_ms": 0, "reason": "No OPENAI_API_KEY"}
        try:
            t0 = time.time()
            self.send([ProviderMessage("user", "ping")], max_tokens=5, temperature=0.0)
            return {"status": "ok", "model": self.model, "latency_ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            return {"status": "error", "model": self.model, "latency_ms": 0, "reason": str(e)}
