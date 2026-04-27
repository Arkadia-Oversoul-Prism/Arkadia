"""SolSpire Oracle — in-memory state stub.

Phase 2 only: a process-local dict of counters. Phase 3 swaps this for a
real persistent store. Tools layer rule (section 6): do not modify, only
ensure the surface stays the same.
"""
from __future__ import annotations

from typing import Any

_STATE: dict[str, Any] = {}


def update_data(parameters: dict[str, Any]) -> dict[str, Any]:
    """Merge `parameters` into the in-memory Oracle state.

    Numeric values accumulate (e.g. logging 100 livestock twice → 200).
    Non-numeric values overwrite. Returns a snapshot of what changed.
    """
    if not isinstance(parameters, dict) or not parameters:
        return {"updated": {}, "snapshot": dict(_STATE)}

    updated: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, (int, float)) and isinstance(_STATE.get(key), (int, float)):
            _STATE[key] = _STATE[key] + value
        else:
            _STATE[key] = value
        updated[key] = _STATE[key]

    return {"updated": updated, "snapshot": dict(_STATE)}


def query_data(parameters: dict[str, Any]) -> dict[str, Any]:
    """Read from Oracle state. If `keys` provided, return that subset; else all."""
    keys = parameters.get("keys") if isinstance(parameters, dict) else None
    if isinstance(keys, list) and keys:
        return {k: _STATE.get(k) for k in keys}
    return dict(_STATE)


def snapshot() -> dict[str, Any]:
    """Full state snapshot for the route response envelope."""
    return dict(_STATE)


def reset() -> None:
    """Test-only: clear all state."""
    _STATE.clear()


__all__ = ["update_data", "query_data", "snapshot", "reset"]
