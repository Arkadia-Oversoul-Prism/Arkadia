"""Deterministic verification-boundary research probe.

No LLM, external side effect, authorization grant, or production acceptance.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()

def verify(resolved: dict, predicate: str, verifier: str) -> dict:
    if resolved.get("resolution", {}).get("status") != "RESOLVED_PENDING_VERIFICATION":
        raise ValueError("verification requires a resolved-pending-verification state")
    if not verifier:
        raise ValueError("verification requires an explicit verifier")

    passed = (
        predicate == "resolution-evidence-supports-claim"
        and resolved["resolution"].get("evidence", {}).get("supports") == resolved.get("claims")
    )

    if predicate != "resolution-evidence-supports-claim":
        status = "UNKNOWN"
    else:
        status = "VERIFIED" if passed else "VERIFICATION_FAILED"

    return {
        "status": status,
        "verifier": verifier,
        "input_resolution_digest": digest(resolved["resolution"]),
        "authority_created": False,
        "acceptance_state": "UNKNOWN",
    }

def run() -> None:
    resolved = {
        "claims": [{"subject": "sample.fact", "value": "A"}],
        "conflicts": [],
        "resolution": {
            "status": "RESOLVED_PENDING_VERIFICATION",
            "evidence": {
                "source_id": "E-100",
                "supports": [{"subject": "sample.fact", "value": "A"}],
            },
            "resolver": "AUTHORIZED_RESOLVER",
        },
        "verification_state": "UNKNOWN",
        "authority_created": False,
    }

    verified = verify(resolved, "resolution-evidence-supports-claim", "INDEPENDENT_VERIFIER")
    assert verified["status"] == "VERIFIED"
    assert verified["acceptance_state"] == "UNKNOWN"
    assert verified["authority_created"] is False

    failed = deepcopy(resolved)
    failed["resolution"]["evidence"]["supports"] = [{"subject": "sample.fact", "value": "B"}]
    failed_result = verify(failed, "resolution-evidence-supports-claim", "INDEPENDENT_VERIFIER")
    assert failed_result["status"] == "VERIFICATION_FAILED"
    assert failed_result["acceptance_state"] == "UNKNOWN"

    unknown = verify(resolved, "unsupported-predicate", "INDEPENDENT_VERIFIER")
    assert unknown["status"] == "UNKNOWN"
    assert unknown["acceptance_state"] == "UNKNOWN"

    # The verifier cannot mutate the resolution record or become its resolver.
    assert resolved["resolution"]["resolver"] == "AUTHORIZED_RESOLVER"

    print("PASS: verification is independent of resolution")
    print("PASS: verification can produce VERIFIED, FAILED, or UNKNOWN")
    print("PASS: verification does not create authority or acceptance")

if __name__ == "__main__":
    run()