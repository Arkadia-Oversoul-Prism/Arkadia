"""N-ATLAS provider adapter for the Engineering Lab.

The adapter speaks the OpenAI-compatible HTTP contract used by self-hosted
N-ATLAS deployments. It never falls back to another model.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from .gateway import ModelAdapter, ModelResponse, ModelUnavailable


class NAtlasAdapter(ModelAdapter):
    provider = "n_atlas"

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 60.0) -> None:
        self._base_url = (base_url or os.environ.get("N_ATLAS_BASE_URL") or "http://localhost:8000/v1").rstrip("/")
        self._api_key = api_key or os.environ.get("N_ATLAS_API_KEY")
        self._timeout = timeout

    def generate(self, *, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **options: Any) -> ModelResponse:
        body: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if tools:
            body["tools"] = tools
        for key in ("temperature", "max_tokens", "top_p"):
            if key in options and options[key] is not None:
                body[key] = options[key]
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        req = urllib.request.Request(f"{self._base_url}/chat/completions", data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ModelUnavailable(f"N-ATLAS inference call failed: {exc}") from exc
        choices = payload.get("choices") or []
        if not choices:
            raise ModelUnavailable("N-ATLAS returned no choices")
        choice = choices[0] or {}
        message = choice.get("message") or {}
        raw_calls = message.get("tool_calls") or []
        tool_calls = [{"name": (call.get("function") or {}).get("name", ""), "arguments": (call.get("function") or {}).get("arguments", {}) or {}} for call in raw_calls]
        return ModelResponse(provider=self.provider, model=payload.get("model") or model, text=message.get("content", "") or "", tool_calls=tool_calls, finish_reason=choice.get("finish_reason", "stop"), usage=payload.get("usage") or {})