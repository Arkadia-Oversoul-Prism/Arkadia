"""SolSpire Phase 4 — Oracle Mutation Layer (real persistence).

Phase 3's oracle was an in-memory dict. Phase 4 makes it a JSON-file
store so that:
  • Transactions, open loops, and asset metadata survive restarts
  • A single thread-safe write path exists for the kernel
  • The next phase can swap this for Supabase/Postgres without
    changing the kernel's call sites

Schema (one JSON file at data/oracle_store.json):

    {
      "transactions": [ {id, ts, amount, currency, party, note, ...} ],
      "open_loops":   [ {id, ts, loop, status, updated_at} ],
      "assets":       [ {id, ts, kind, count, prompt, refs} ],
      "balance":      { "<currency>": <number>, ... },
      "events":       [ {ts, kind, payload} ]
    }
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import Any

_DATA_DIR = os.environ.get("SOLSPIRE_DATA_DIR", "data")
_STORE_PATH = os.path.join(_DATA_DIR, "oracle_store.json")
_LOCK = threading.Lock()

_DEFAULT: dict[str, Any] = {
    "transactions": [],
    "open_loops":   [],
    "assets":       [],
    "balance":      {},
    "events":       [],
}


def _ensure_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def _read() -> dict[str, Any]:
    _ensure_dir()
    if not os.path.exists(_STORE_PATH):
        return json.loads(json.dumps(_DEFAULT))  # deep copy
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(_DEFAULT))
    # Backfill any missing top-level keys
    for k, v in _DEFAULT.items():
        data.setdefault(k, json.loads(json.dumps(v)))
    return data


def _write(data: dict[str, Any]) -> None:
    _ensure_dir()
    tmp = _STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _STORE_PATH)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _now() -> float:
    return time.time()


# ── Public mutators ─────────────────────────────────────────────────────────

def write_to_oracle(data: dict[str, Any]) -> dict[str, Any]:
    """Append a generic event row. Spec section 4. Always returns
    {status: 'written', ...} so verify() can confirm success.
    """
    with _LOCK:
        store = _read()
        event = {
            "id":      _new_id("evt"),
            "ts":      _now(),
            "payload": data if isinstance(data, dict) else {"value": data},
        }
        store["events"].append(event)
        _write(store)
    return {"status": "written", "event_id": event["id"], "data": data}


def write_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    amount = payload.get("amount")
    try:
        amount_n = float(amount) if amount is not None else 0.0
    except (TypeError, ValueError):
        amount_n = 0.0
    currency = (payload.get("currency") or "USD").upper()
    txn = {
        "id":       _new_id("txn"),
        "ts":       _now(),
        "amount":   amount_n,
        "currency": currency,
        "party":    payload.get("party"),
        "note":     payload.get("note"),
    }
    with _LOCK:
        store = _read()
        store["transactions"].append(txn)
        store["events"].append({
            "id": _new_id("evt"), "ts": _now(),
            "payload": {"kind": "transaction", "transaction_id": txn["id"]},
        })
        _write(store)
    return {"status": "written", "transaction": txn}


def update_balance(payload: dict[str, Any]) -> dict[str, Any]:
    """Re-derive balance from the recorded transaction list per currency.
    Idempotent: calling repeatedly gives the same result for the same data.
    """
    with _LOCK:
        store = _read()
        balances: dict[str, float] = {}
        for t in store["transactions"]:
            cur = (t.get("currency") or "USD").upper()
            balances[cur] = round(balances.get(cur, 0.0) + float(t.get("amount", 0.0)), 4)
        store["balance"] = balances
        _write(store)
    return {"status": "success", "balance": balances}


def update_open_loops(payload: dict[str, Any]) -> dict[str, Any]:
    loop_text = (payload.get("loop") or "").strip()
    if not loop_text:
        return {"status": "skipped", "reason": "empty loop text"}
    new_status = (payload.get("status") or "open").lower()
    with _LOCK:
        store = _read()
        # Update existing entry if loop text matches; else append new.
        match = next((l for l in store["open_loops"] if l.get("loop") == loop_text), None)
        if match:
            match["status"]     = new_status
            match["updated_at"] = _now()
            row = match
        else:
            row = {
                "id":         _new_id("loop"),
                "ts":         _now(),
                "loop":       loop_text,
                "status":     new_status,
                "updated_at": _now(),
            }
            store["open_loops"].append(row)
        _write(store)
    return {"status": "written", "loop": row}


def store_asset(payload: dict[str, Any], refs: list[Any] | None = None) -> dict[str, Any]:
    asset = {
        "id":     _new_id("asset"),
        "ts":     _now(),
        "kind":   payload.get("kind", "image"),
        "count":  int(payload.get("count", 1) or 1),
        "prompt": payload.get("prompt"),
        "refs":   list(refs or []),
    }
    with _LOCK:
        store = _read()
        store["assets"].append(asset)
        _write(store)
    return {"status": "written", "asset": asset}


def log_event(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    return write_to_oracle({"kind": kind, **(payload or {})})


# ── Read helpers ────────────────────────────────────────────────────────────

def snapshot() -> dict[str, Any]:
    return _read()


def reset() -> None:
    """Test-only: clear the store file."""
    with _LOCK:
        _write(json.loads(json.dumps(_DEFAULT)))


__all__ = [
    "write_to_oracle", "write_transaction", "update_balance",
    "update_open_loops", "store_asset", "log_event",
    "snapshot", "reset",
]
