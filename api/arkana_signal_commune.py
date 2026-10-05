"""Arkana Signal Commune runtime seam extracted from api.main."""
from __future__ import annotations
import json
import httpx

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

async def gemini_signal_chat(
    messages: list[dict],
    system: str,
    signal: dict,
    audio_b64: str | None = None,
    mime_type: str = "audio/webm",
    api_key: str | None = None,
) -> str:
    from api.key_pool import acquire_key, report_failure, report_success
    current_key = api_key or acquire_key()
    if not current_key:
        return None
    signal_context = json.dumps(signal, ensure_ascii=False)
    contents = []
    for m in messages:
        role = "model" if m.get("role") in ("oracle", "assistant") else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    if contents:
        evidence_parts = [{
            "text": (
                "ARKANA SIGNAL EVIDENCE PACKAGE.\n"
                "The Signal Object is derived interpretation, not source fact. "
                "Do not promote candidates or unresolved references into facts. "
                "The original audio, when present, is the primary source evidence.\n\n"
                + signal_context
            )
        }]
        if audio_b64:
            evidence_parts.append({"inline_data": {"mime_type": mime_type, "data": audio_b64}})
        contents[-1]["parts"].extend(evidence_parts)
    payload = {
        "system_instruction": {"parts": [{"text": (
            system + "\n\n== SIGNAL FABRIC BOUNDARY ==\n"
            "You have been given a canonical Arkana Signal Object. "
            "Treat SOURCE, DERIVED, CANDIDATE, and CONTEXT as distinct epistemic classes. "
            "Unknown remains unknown. Human authority remains absolute."
        )}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.88, "maxOutputTokens": 16384},
    }
    tried: set[str] = set()
    last_err = None
    async with httpx.AsyncClient(timeout=90) as client:
        while current_key and len(tried) < 8:
            tried.add(current_key)
            for model in GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (429, 403):
                        last_err = resp.text
                        break
                    resp.raise_for_status()
                    data = resp.json()
                    report_success(current_key)
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    last_err = str(e)
            report_failure(current_key)
            current_key = acquire_key()
            if current_key in tried:
                break
    raise Exception(f"All Gemini signal models failed. Last error: {last_err}")
