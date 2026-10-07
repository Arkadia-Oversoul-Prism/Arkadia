"""N-ATLAS provider adapter for the Engineering Lab.

The adapter speaks the OpenAI-compatible HTTP contract used by self-hosted
N-ATLAS deployments. It never falls back to another model.
"""

from __future__ import annotations

import json
import os
import urllib.error
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

class NAtlasGradioAdapter(ModelAdapter):
    """Adapter for the public Gradio runtime contract used by N-ATLaS."""

    provider = "n_atlas"

    def __init__(self, base_url: str | None = None, timeout: float = 300.0) -> None:
        self._base_url = (base_url or os.environ.get("N_ATLAS_BASE_URL") or "").rstrip("/")
        self._timeout = timeout

    def generate(self, *, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **options: Any) -> ModelResponse:
        if not self._base_url:
            raise ModelUnavailable("N-ATLaS Gradio runtime is not configured")
        data = [
            json.dumps(messages, ensure_ascii=False),
            float(options.get("temperature", 0.0)),
            int(options.get("max_tokens", 128)),
            bool(options.get("json_mode", False)),
        ]
        req = urllib.request.Request(
            f"{self._base_url}/gradio_api/call/generate",
            data=json.dumps({"data": data}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            event_id = payload.get("event_id")
            if not event_id:
                raise ModelUnavailable("N-ATLaS Gradio runtime returned no event_id")
            stream_req = urllib.request.Request(
                f"{self._base_url}/gradio_api/call/generate/{event_id}",
                headers={"Accept": "text/event-stream"},
                method="GET",
            )
            response_text = ""
            with urllib.request.urlopen(stream_req, timeout=self._timeout) as stream:
                while True:
                    line = stream.readline()
                    if not line:
                        break
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", errors="replace")
                    line = line.strip()
                    if not line.startswith("data: "):
                        continue
                    data_text = line[6:]
                    if data_text == "[DONE]":
                        break
                    try:
                        event_data = json.loads(data_text)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event_data, list) or not event_data:
                        continue
                    value = event_data[0]
                    if isinstance(value, str):
                        try:
                            parsed = json.loads(value)
                        except json.JSONDecodeError:
                            response_text = value.strip()
                        else:
                            if isinstance(parsed, dict):
                                response_text = str(parsed.get("text") or parsed.get("response") or parsed.get("output") or "").strip()
                            else:
                                response_text = str(parsed).strip()
                    elif isinstance(value, dict):
                        response_text = str(value.get("text") or value.get("response") or value.get("output") or "").strip()
                    if response_text:
                        break
            if not response_text:
                raise ModelUnavailable("N-ATLaS Gradio runtime returned no usable text")
            return ModelResponse(
                provider=self.provider,
                model=model,
                text=response_text,
                finish_reason="stop",
                usage={"protocol": "gradio", "endpoint": "/gradio_api/call/generate"},
            )
        except ModelUnavailable:
            raise
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise ModelUnavailable(f"N-ATLaS Gradio inference call failed: {exc}") from exc

