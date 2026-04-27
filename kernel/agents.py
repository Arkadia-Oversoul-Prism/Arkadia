"""SolSpire Phase 4 — internal agent functions.

Thin, deterministic wrappers the Execution Engine calls. Each one
returns an envelope with a `status` field so verify() can check it.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from api import arkadia_engine as arkadia
from kernel import oracle_store


def call_image_agent(payload: dict[str, Any]) -> dict[str, Any]:
    """Phase 4 keeps image generation stubbed (real provider lives outside
    the kernel). Returns descriptors that store_asset can persist.
    """
    try:
        count = int(payload.get("count", 1) or 1)
    except (TypeError, ValueError):
        count = 1
    count = max(1, min(count, 50))
    prompt = (payload.get("prompt") or "").strip() or "default arkadia visual"
    images = [
        {"id": f"img_{uuid.uuid4().hex[:8]}", "prompt": prompt, "status": "stubbed"}
        for _ in range(count)
    ]
    return {"status": "success", "kind": "image", "count": count, "images": images}


def store_asset(payload: dict[str, Any], image_result: dict[str, Any]) -> dict[str, Any]:
    refs = image_result.get("images") if isinstance(image_result, dict) else None
    return oracle_store.store_asset(
        {
            "kind":   "image",
            "count":  image_result.get("count", payload.get("count", 1)),
            "prompt": payload.get("prompt"),
        },
        refs=refs,
    )


def write_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    return oracle_store.write_transaction(payload)


def update_balance(payload: dict[str, Any]) -> dict[str, Any]:
    return oracle_store.update_balance(payload)


def update_open_loops(payload: dict[str, Any]) -> dict[str, Any]:
    return oracle_store.update_open_loops(payload)


def generate_verse(_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    verse = arkadia.generate_verse()
    return {
        "status": "success",
        "verse":  verse,
        "lines":  verse.split("\n"),
        "engine": "arkadia.symbolic.v1",
    }


def log_event(payload: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    return oracle_store.log_event(
        kind=str((context or {}).get("kind", "kernel_event")),
        payload={"payload": payload, "ts": time.time(), "context": context or {}},
    )


__all__ = [
    "call_image_agent", "store_asset",
    "write_transaction", "update_balance",
    "update_open_loops", "generate_verse",
    "log_event",
]
