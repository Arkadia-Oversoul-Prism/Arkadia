"""
Arkadia Knowledge OS — Gemini Provider Adapter
===============================================
Implements BaseProvider for Google Gemini.
Resolves API key per-call (supports key rotation via api/key_manager.py).
Business logic lives in Oracle/Kernel, NOT here.
"""

import os
import time
from typing import AsyncIterator, Optional

from providers.base import BaseProvider, ProviderMessage, ProviderResponse


class GeminiProvider(BaseProvider):
    name = "gemini"
    display_name = "Google Gemini"

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model

    def _get_key(self) -> Optional[str]:
        """Resolve API key via key_manager rotation if available, else env var."""
        try:
            from api.key_manager import get_next_key
            return get_next_key()
        except Exception:
            return os.environ.get("GEMINI_API_KEY", "") or None

    def _configured_genai(self):
        """Return genai configured with a fresh key per call — supports rotation."""
        import google.generativeai as genai
        key = self._get_key()
        if key:
            genai.configure(api_key=key)
        return genai

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
        genai = self._configured_genai()

        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt or None,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        # Build Gemini-format history from all messages except the last user turn.
        # Gemini expects alternating user/model roles in history.
        history: list[dict] = []
        for msg in messages[:-1]:
            role = "model" if msg.role == "assistant" else "user"
            history.append({"role": role, "parts": [msg.content]})

        # The final message is sent as the live turn
        last_msg = messages[-1] if messages else ProviderMessage("user", "")

        t0 = time.time()
        if history:
            chat = model.start_chat(history=history)
            response = chat.send_message(last_msg.content)
        else:
            response = model.generate_content(last_msg.content)

        latency_ms = int((time.time() - t0) * 1000)
        text = response.text if hasattr(response, "text") else str(response)

        usage = getattr(response, "usage_metadata", None)
        return ProviderResponse(
            content=text,
            model=self.model,
            provider_name=self.name,
            prompt_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
            completion_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
            raw={"latency_ms": latency_ms},
        )

    async def stream(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        genai = self._configured_genai()
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt or None,
            generation_config={"temperature": temperature},
        )
        last_content = messages[-1].content if messages else ""
        response = model.generate_content(last_content, stream=True)
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text

    def models(self) -> list[str]:
        return [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]

    def capabilities(self) -> list[str]:
        return ["chat", "stream", "embed", "vision", "search"]

    def health(self) -> dict:
        if not self.authenticate():
            return {
                "status": "unconfigured",
                "model": self.model,
                "latency_ms": 0,
                "reason": "No GEMINI_API_KEY configured",
            }
        try:
            t0 = time.time()
            response = self.send(
                [ProviderMessage("user", "ping")],
                max_tokens=5,
                temperature=0.0,
            )
            return {
                "status": "ok",
                "model": self.model,
                "latency_ms": response.raw.get("latency_ms", 0),
            }
        except Exception as e:
            return {
                "status": "error",
                "model": self.model,
                "latency_ms": 0,
                "reason": str(e),
            }
