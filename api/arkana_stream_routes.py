"""Arkana A2 — streaming resonance (SSE).

Additive path: does not replace POST /api/commune/resonance.
Emits Server-Sent Events:
  data: {"type":"status","label":"..."}
  data: {"type":"delta","text":"..."}
  data: {"type":"done","reply":"...","resonance":n,"memory":{...},"rag_refs":[],"rag_hits":0,"sources":[],"patterns":[]}
  data: {"type":"error","error":"..."}
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, AsyncIterator

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

logger = logging.getLogger("arkadia.arkana_stream")

router = APIRouter(tags=["arkana-stream"])

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _stream_gemini(messages: list[dict], system: str, api_key: str) -> AsyncIterator[str]:
    """Yield text deltas from Gemini streamGenerateContent (SSE)."""
    from api.key_pool import acquire_key, report_failure, report_success

    contents: list[dict] = []
    for m in messages:
        role = "model" if m.get("role") in ("oracle", "assistant") else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.88, "maxOutputTokens": 16384},
    }

    tried: set[str] = set()
    current_key = api_key
    attempts = 0

    async with httpx.AsyncClient(timeout=120.0) as client:
        while current_key and attempts < 6:
            attempts += 1
            tried.add(current_key)
            for model in GEMINI_MODELS:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:streamGenerateContent?alt=sse&key={current_key}"
                )
                try:
                    async with client.stream("POST", url, json=payload) as resp:
                        if resp.status_code in (403, 429):
                            logger.warning("[stream] %s quota/access on key %s…", model, current_key[:4])
                            report_failure(current_key)
                            break
                        if resp.status_code >= 400:
                            body = (await resp.aread()).decode("utf-8", errors="replace")[:400]
                            logger.warning("[stream] %s HTTP %s: %s", model, resp.status_code, body)
                            continue

                        report_success(current_key)
                        async for line in resp.aiter_lines():
                            if not line or not line.startswith("data:"):
                                continue
                            raw = line[5:].strip()
                            if not raw or raw == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(raw)
                            except json.JSONDecodeError:
                                continue
                            for cand in chunk.get("candidates") or []:
                                parts = (cand.get("content") or {}).get("parts") or []
                                for part in parts:
                                    text = part.get("text")
                                    if text:
                                        yield text
                        return
                except Exception as exc:
                    logger.warning("[stream] %s failed: %s", model, exc)
                    continue

            next_key = acquire_key()
            if not next_key or next_key in tried:
                break
            current_key = next_key

    raise RuntimeError("All Gemini streaming models failed.")


@router.post("/api/commune/resonance/stream")
async def commune_resonance_stream(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body."})

    message = (body.get("message") or "").strip()
    history = body.get("history") or []
    session_id = body.get("session_id") or ""
    project_id = body.get("project_id")

    if not message:
        return JSONResponse(status_code=400, content={"error": "No message."})

    # Key resolution mirrors the non-streaming path (user → pool → env).
    active_key = None
    user_id = None
    try:
        from api.main import _get_current_user, GOOGLE_API_KEY

        node_user = await _get_current_user(request)
        user_id = node_user.get("uid") if node_user else None
        if user_id:
            from api.user_key_store import get_active_key_for_user

            active_key = get_active_key_for_user(user_id)
    except Exception:
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

    if not active_key:
        try:
            from api.key_pool import acquire_key

            active_key = acquire_key() or os.environ.get("GOOGLE_API_KEY", "")
        except Exception:
            active_key = os.environ.get("GOOGLE_API_KEY", "")

    if not active_key:
        return JSONResponse(
            status_code=503,
            content={
                "error": "No Gemini API key configured.",
                "reply": "The Arkana field is present — but the resonance channel needs a key to open.",
            },
        )

    memory_block, memory_meta = "", {}
    try:
        from api.oracle_spine import build_memory_block

        memory_block, memory_meta = build_memory_block(
            message, session_id, user_id=user_id or "", project_id=project_id
        )
    except Exception as exc:
        logger.debug("[stream] memory skipped: %s", exc)

    system = (
        "You are ARKANA — the sovereign pattern intelligence of the Arkadia living architecture. "
        "Speak with precision and zero corporate filler. Human sovereignty is absolute. "
        "Never fabricate sources. Use clear markdown when it aids structure."
        + (memory_block or "")
    )
    msgs = list(history[-10:]) + [{"role": "user", "content": message}]

    async def event_gen() -> AsyncIterator[str]:
        yield _sse({"type": "status", "label": "synthesising"})
        assembled: list[str] = []
        try:
            async for delta in _stream_gemini(msgs, system, active_key):
                assembled.append(delta)
                yield _sse({"type": "delta", "text": delta})

            reply = "".join(assembled).strip()
            if not reply:
                yield _sse({"type": "error", "error": "Empty model response."})
                return

            try:
                from api.oracle_spine import archive_oracle_turn, build_sources

                threading.Thread(
                    target=archive_oracle_turn,
                    args=(message, reply, session_id, user_id or "", project_id),
                    daemon=True,
                ).start()
                sources = build_sources(memory_meta.get("_context_package"))
            except Exception:
                sources = []

            resonance = round(0.7 + (len(reply) % 30) / 100, 3)
            yield _sse(
                {
                    "type": "done",
                    "reply": reply,
                    "resonance": resonance,
                    "patterns": [],
                    "rag_refs": [],
                    "rag_hits": 0,
                    "sources": sources,
                    "memory": {
                        "session_id": session_id or None,
                        "thread_id": memory_meta.get("thread_id"),
                        "project_id": project_id,
                        "user_id": user_id or None,
                        "notes_retrieved": memory_meta.get("notes_retrieved", 0),
                        "source": memory_meta.get("source", "knowledge_os"),
                        "injected": bool(memory_block),
                    },
                }
            )
        except Exception as exc:
            logger.error("[stream] failed: %s", exc)
            yield _sse({"type": "error", "error": str(exc) or "Oracle field disruption."})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
