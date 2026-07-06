"""
Arkadia Knowledge OS — Anthropic Claude Provider Adapter
=========================================================
Implements BaseProvider for Claude via the official anthropic SDK.
Business logic lives in Oracle/Kernel, NOT here.
"""

import os
import time
from typing import AsyncIterator, Optional

from providers.base import BaseProvider, ProviderMessage, ProviderResponse


class ClaudeProvider(BaseProvider):
    name = "claude"
    display_name = "Anthropic Claude"

    def __init__(self, model: str = "claude-opus-4-5"):
        self.model = model

    def _get_key(self) -> Optional[str]:
        return os.environ.get("ANTHROPIC_API_KEY", "") or None

    def _get_client(self):
        import anthropic
        key = self._get_key()
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        return anthropic.Anthropic(api_key=key)

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

        # Anthropic API only accepts "user" and "assistant" in messages[].
        # "system" role is passed as the top-level `system` parameter (already handled above).
        # Merge any inline system messages into the system_prompt, then exclude them from messages[].
        extra_system: list[str] = []
        anthropic_messages = []
        for msg in messages:
            if msg.role == "system":
                extra_system.append(msg.content)
            elif msg.role in ("user", "assistant"):
                anthropic_messages.append({"role": msg.role, "content": msg.content})

        if extra_system:
            merged = "\n\n".join(filter(None, [system_prompt or ""] + extra_system))
            system_prompt = merged or None

        t0 = time.time()
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=anthropic_messages,
        )
        latency_ms = int((time.time() - t0) * 1000)

        content = response.content[0].text if response.content else ""
        return ProviderResponse(
            content=content,
            model=self.model,
            provider_name=self.name,
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            raw={"latency_ms": latency_ms, "stop_reason": response.stop_reason},
        )

    async def stream(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        anthropic_messages = [
            {"role": "assistant" if m.role == "assistant" else "user", "content": m.content}
            for m in messages
        ]
        # Filter out system messages (handled by system= param)
        clean_messages = [
            {"role": m.role, "content": m.content}
            for m in messages if m.role in ("user", "assistant")
        ]
        with client.messages.stream(
            model=self.model,
            max_tokens=2048,
            temperature=temperature,
            system=system_prompt or "",
            messages=clean_messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def models(self) -> list[str]:
        return ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-3-5"]

    def capabilities(self) -> list[str]:
        return ["chat", "stream", "vision"]

    def health(self) -> dict:
        if not self.authenticate():
            return {"status": "unconfigured", "model": self.model, "latency_ms": 0, "reason": "No ANTHROPIC_API_KEY"}
        try:
            t0 = time.time()
            self.send([ProviderMessage("user", "ping")], max_tokens=5, temperature=0.0)
            return {"status": "ok", "model": self.model, "latency_ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            return {"status": "error", "model": self.model, "latency_ms": 0, "reason": str(e)}
