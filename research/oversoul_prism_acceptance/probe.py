"""Deterministic acceptance-to-WorkEvent boundary probe.

No LLM, external side effect, or production runtime is used.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()

def accept(verified: dict, acceptance: dict) -> dict:
    if verified.get("status") != "VERIFIED":
        raise ValueError("acceptance requires VERIFIED input")
    if not acceptance.get("accepting_authority"):
        raise ValueError("acceptance requires explicit accepting authority")
    if not acceptance.get("authorization_scope"):
        raise ValueError("acceptance requires explicit acceptance scope")

    return {
        "status": "ACCEPTED",
        "accepted_result_digest": digest(verified),
        "accepting_authority": acceptance["accepting_authority"],
        "authorization_scope": acceptance["authorization_scope"],
        "execution_authorization": acceptance.get("execution_authorization"),
    }

def execute(accepted: dict, action: str) -> dict:
    execution_auth = accepted.get("execution_authorization")
    if not execution_auth:
        raise ValueError("execution requires explicit execution authorization")
    if execution_auth.get("action") != action:
        raise ValueError("execution action is outside accepted authorization")

    return {
        "status": "EXECUTED",
        "action": action,
        "acceptance_digest": digest(accepted),
        "execution_authorization": execution_auth,
    }

def create_work_event(execution: dict) -> dict:
    if execution.get("status") != "EXECUTED":
        raise ValueError("WorkEvent requires an observed execution")

    return {
        "event_type": "CONSEQUENTIAL_STATE_TRANSITION",
        "execution_digest": digest(execution),
        "authority_created": False,
        "completion_state": "UNKNOWN",
        "review_state": "UNKNOWN",
    }

def run() -> None:
    verified = {
        "status": "VERIFIED",
        "claim": {"subject": "sample.fact", "value": "A"},
        "verification_id": "VER-100",
    }

    accepted_without_execution = accept(
        verified,
        {
            "accepting_authority": "HUMAN-AUTHORITY",
            "authorization_scope": "sample.project",
        },
    )
    try:
        execute(accepted_without_execution, "publish")
        raise AssertionError("execution must require explicit execution authorization")
    except ValueError:
        pass

    accepted = accept(
        verified,
        {
            "accepting_authority": "HUMAN-AUTHORITY",
            "authorization_scope": "sample.project",
            "execution_authorization": {
                "authorization_id": "AUTH-200",
                "action": "publish",
                "scope": "sample.project",
            },
        },
    )

    execution = execute(accepted, "publish")
    assert execution["status"] == "EXECUTED"
    event = create_work_event(execution)
    assert event["event_type"] == "CONSEQUENTIAL_STATE_TRANSITION"
    assert event["authority_created"] is False
    assert event["completion_state"] == "UNKNOWN"
    assert event["review_state"] == "UNKNOWN"

    print("PASS: acceptance does not imply execution")
    print("PASS: execution requires explicit bounded authorization")
    print("PASS: WorkEvent records consequence without creating authority")

if __name__ == "__main__":
    run()