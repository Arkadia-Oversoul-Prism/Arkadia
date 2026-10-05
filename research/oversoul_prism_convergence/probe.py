"""Deterministic branch-convergence research probe for the Oversoul Prism.

This is a research model, not a runtime executor.
No LLM, authorization, WorkEvent, or external side effect is used.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()

def branch_transform(state: dict, function_id: str, layer: int) -> dict:
    out = deepcopy(state)
    out["branch_provenance"] = [
        *out.get("branch_provenance", []),
        {
            "node_id": f"{function_id}-L{layer:02d}",
            "input_digest": digest(state),
        },
    ]
    out["branch_provenance"][-1]["output_digest"] = digest(out)
    return out

def converge(states: list[dict]) -> dict:
    if not states:
        raise ValueError("convergence requires at least one state")

    claims_by_key: dict[str, set[str]] = {}
    for state in states:
        for claim in state.get("claims", []):
            key = claim["subject"]
            claims_by_key.setdefault(key, set()).add(claim["value"])

    claims = []
    conflicts = []
    for subject, values in sorted(claims_by_key.items()):
        if len(values) == 1:
            claims.append({"subject": subject, "value": next(iter(values))})
        else:
            conflicts.append({"subject": subject, "values": sorted(values)})

    evidence = sorted(
        {json.dumps(e, sort_keys=True) for s in states for e in s.get("evidence", [])}
    )
    unknowns = sorted({u for s in states for u in s.get("unknowns", [])})
    provenance = [p for s in states for p in s.get("branch_provenance", [])]

    return {
        "claims": claims,
        "evidence": [json.loads(e) for e in evidence],
        "unknowns": unknowns,
        "conflicts": conflicts,
        "branch_provenance": provenance,
        "verification_state": "UNKNOWN",
        "authority_created": False,
        "external_side_effect": False,
    }

def run() -> None:
    source = {
        "claims": [{"subject": "sample.fact", "value": "canonical"}],
        "evidence": [{"source_id": "E-001", "text": "observed input"}],
        "unknowns": ["sample.verification"],
        "branch_provenance": [],
        "authority_created": False,
    }

    outputs = []
    for function_id in ("A01", "A02", "A03"):
        state = source
        for layer in (1, 2, 3):
            state = branch_transform(state, function_id, layer)
        outputs.append(state)

    result = converge(outputs)
    assert result["claims"] == [{"subject": "sample.fact", "value": "canonical"}]
    assert result["evidence"] == source["evidence"]
    assert result["unknowns"] == source["unknowns"]
    assert len(result["branch_provenance"]) == 9
    assert result["verification_state"] == "UNKNOWN"
    assert result["authority_created"] is False
    assert result["external_side_effect"] is False
    assert not result["conflicts"]

    contradictory = deepcopy(outputs)
    contradictory[1]["claims"] = [{"subject": "sample.fact", "value": "different"}]
    conflict_result = converge(contradictory)
    assert not conflict_result["claims"]
    assert conflict_result["conflicts"] == [{"subject": "sample.fact", "values": ["canonical", "different"]}]
    assert conflict_result["verification_state"] == "UNKNOWN"

    print("PASS: agreement preserves evidence, UNKNOWN, provenance, and authority boundary")
    print("PASS: contradiction remains explicit and unresolved")

if __name__ == "__main__":
    run()