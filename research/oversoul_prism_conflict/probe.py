"""Deterministic conflict propagation and resolution-boundary probe.

No LLM, authorization grant, WorkEvent, or external side effect is used.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()

def propagate(state: dict, node_id: str) -> dict:
    out = deepcopy(state)
    record = {
        "node_id": node_id,
        "input_digest": digest(state),
        "preserved_conflict": bool(state.get("conflicts")),
    }
    record["output_digest"] = digest(out)
    out["provenance"] = [*out.get("provenance", []), record]
    # A propagation node cannot resolve or canonicalize an unresolved conflict.
    out["verification_state"] = "UNKNOWN"
    out["authority_created"] = False
    return out

def resolve(state: dict, resolution_evidence: dict | None, resolver: str | None) -> dict:
    if not state.get("conflicts"):
        raise ValueError("resolution requires an unresolved conflict")
    if not resolution_evidence or not resolver:
        raise ValueError("resolution requires explicit evidence and resolver")

    out = deepcopy(state)
    out["resolution"] = {
        "status": "RESOLVED",
        "evidence": resolution_evidence,
        "resolver": resolver,
        "input_conflict_digest": digest(state["conflicts"]),
    }
    out["conflicts"] = []
    out["claims"] = [resolution_evidence["resolved_claim"]]
    out["verification_state"] = "UNKNOWN"
    out["authority_created"] = False
    return out

def run() -> None:
    conflicted = {
        "claims": [],
        "conflicts": [{"subject": "sample.fact", "values": ["canonical", "different"]}],
        "evidence": [{"source_id": "E-001", "text": "observed input"}],
        "unknowns": ["sample.verification"],
        "provenance": [],
        "verification_state": "UNKNOWN",
        "authority_created": False,
    }

    state = conflicted
    for node_id in ("A01-L04", "A02-L05", "A03-L06", "A01-L07"):
        state = propagate(state, node_id)

    assert state["claims"] == []
    assert state["conflicts"] == conflicted["conflicts"]
    assert state["verification_state"] == "UNKNOWN"
    assert state["authority_created"] is False
    assert len(state["provenance"]) == 4
    assert all(p["preserved_conflict"] for p in state["provenance"])

    resolved = resolve(
        state,
        {
            "source_id": "E-002",
            "text": "independent resolving evidence",
            "resolved_claim": {"subject": "sample.fact", "value": "canonical"},
        },
        "EXPLICIT_RESOLVER_REQUIRED",
    )

    assert resolved["conflicts"] == []
    assert resolved["claims"] == [{"subject": "sample.fact", "value": "canonical"}]
    assert resolved["resolution"]["status"] == "RESOLVED"
    assert resolved["resolution"]["resolver"] == "EXPLICIT_RESOLVER_REQUIRED"
    assert resolved["verification_state"] == "UNKNOWN"
    assert resolved["authority_created"] is False

    try:
        resolve(state, None, None)
        raise AssertionError("resolution without evidence/resolver must fail")
    except ValueError:
        pass

    print("PASS: unresolved conflict survives later transformations")
    print("PASS: propagation cannot synthesize a canonical claim")
    print("PASS: resolution requires explicit evidence and resolver")

if __name__ == "__main__":
    run()