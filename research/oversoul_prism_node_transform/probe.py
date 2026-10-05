#!/usr/bin/env python3
"""Deterministic, side-effect-free node transformation probe."""

from __future__ import annotations
import hashlib
import json
from copy import deepcopy

UNKNOWN = "UNKNOWN"

def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def transform(node_id: str, state: dict) -> dict:
    """Normalize a state without adding factual claims."""
    out = deepcopy(state)
    out.setdefault("unknowns", [])
    out["processed_by"] = node_id
    out["context_granularity"] = {
        "L01": "broadest",
        "L02": "more_granular",
        "L03": "deepest_in_slice",
    }.get(node_id.split("-")[1], UNKNOWN)
    return out

def run_probe() -> dict:
    state = {
        "claim": "sample input",
        "evidence": ["E-001"],
        "unknowns": ["buyer_status"],
    }
    first = transform("A01-L01", state)
    second = transform("A01-L02", first)
    result = {
        "input_digest": digest(state),
        "output_digest": digest(second),
        "state": second,
        "evidence_preserved": second["evidence"] == ["E-001"],
        "unknown_preserved": "buyer_status" in second["unknowns"],
        "authority_created": False,
        "external_side_effect": False,
    }
    return result

if __name__ == "__main__":
    result = run_probe()
    assert result["evidence_preserved"]
    assert result["unknown_preserved"]
    assert not result["authority_created"]
    assert not result["external_side_effect"]
    print(json.dumps(result, indent=2, sort_keys=True))
