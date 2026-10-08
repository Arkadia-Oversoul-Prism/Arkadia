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
    """Adapter for the public Gradio runtime contract used by N-ATLaS.

    Gradio's queued HTTP API is an SSE protocol: POST returns an event id,
    then GET returns named events (generating, complete, error, heartbeat).
    The adapter consumes the event type explicitly so an error frame can never
    be mistaken for model text and a later complete frame can replace partial
    output.
    """

    provider = "n_atlas"

    def __init__(self, base_url: str | None = None, timeout: float = 300.0) -> None:
        self._base_url = (base_url or os.environ.get("N_ATLAS_BASE_URL") or "").rstrip("/")
        self._timeout = timeout

    @staticmethod
    def _extract_text(value: Any) -> str:
        """Extract text from the common Gradio output shapes without guessing."""
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return ""
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return text
            if parsed != value:
                return NAtlasGradioAdapter._extract_text(parsed)
            return text
        if isinstance(value, dict):
            for key in ("text", "response", "output", "content"):
                if key in value:
                    text = NAtlasGradioAdapter._extract_text(value[key])
                    if text:
                        return text
            message = value.get("message")
            if message is not None:
                text = NAtlasGradioAdapter._extract_text(message)
                if text:
                    return text
            return ""
        if isinstance(value, (list, tuple)):
            for item in value:
                text = NAtlasGradioAdapter._extract_text(item)
                if text:
                    return text
        return ""

    @staticmethod
    def _sse_frames(stream: Any):
        """Yield (event_type, data_text) from an SSE response stream."""
        event_type = "message"
        data_lines: list[str] = []
        while True:
            raw = stream.readline()
            if not raw:
                if data_lines:
                    yield event_type, "\n".join(data_lines)
                break
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            line = raw.rstrip("\r\n")
            if not line:
                if data_lines:
                    yield event_type, "\n".join(data_lines)
                event_type = "message"
                data_lines = []
                continue
            if line.startswith("event:"):
                event_type = line[6:].strip() or "message"
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif line.startswith(":"):
                continue

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
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
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
            seen_events: list[str] = []
            terminal_event = ""
            with urllib.request.urlopen(stream_req, timeout=self._timeout) as stream:
                for event_type, data_text in self._sse_frames(stream):
                    seen_events.append(event_type)
                    if data_text == "[DONE]":
                        terminal_event = event_type
                        break
                    try:
                        event_data = json.loads(data_text)
                    except json.JSONDecodeError:
                        event_data = data_text

                    if event_type == "error":
                        detail = self._extract_text(event_data) or data_text.strip() or "unknown Gradio error"
                        raise ModelUnavailable(f"N-ATLaS Gradio runtime error: {detail}")

                    candidate = self._extract_text(event_data)
                    if candidate:
                        response_text = candidate

                    if event_type == "complete":
                        terminal_event = event_type
                        break

            if not response_text:
                events = ",".join(seen_events) or "none"
                raise ModelUnavailable(
                    f"N-ATLaS Gradio runtime returned no usable text "
                    f"(event_id={event_id}, events={events})"
                )

            return ModelResponse(
                provider=self.provider,
                model=model,
                text=response_text,
                finish_reason="stop",
                usage={
                    "protocol": "gradio",
                    "endpoint": "/gradio_api/call/generate",
                    "event_id": event_id,
                    "sse_events": seen_events,
                    "terminal_event": terminal_event or (seen_events[-1] if seen_events else ""),
                },
            )
        except ModelUnavailable:
            raise
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            raise ModelUnavailable(f"N-ATLaS Gradio inference call failed: {exc}") from exc
