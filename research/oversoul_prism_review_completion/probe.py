"""Deterministic WorkEvent review, completion, and production-acceptance boundary probe.

No LLM, external side effect, or production runtime is used.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()


def create_work_event(execution: dict) -> dict:
    if execution.get("status") != "EXECUTED":
        raise ValueError("WorkEvent requires observed execution")

    event = {
        "event_type": "CONSEQUENTIAL_STATE_TRANSITION",
        "execution_digest": digest(execution),
        "completion_state": "UNKNOWN",
        "review_state": "REVIEW_PENDING",
        "authority_created": False,
    }
    event["event_digest"] = digest(event)
    return event


def review_work_event(event: dict, outcome: str, reviewer: str) -> dict:
    if event.get("review_state") != "REVIEW_PENDING":
        raise ValueError("event is not pending review")
    if outcome not in {
        "ACCEPTED",
        "REJECTED",
        "AMENDMENT_REQUIRED",
        "MORE_EVIDENCE_REQUIRED",
    }:
        raise ValueError("invalid review outcome")
    if not reviewer:
        raise ValueError("review requires explicit reviewer")

    return {
        "record_type": "REVIEW",
        "work_event_digest": event["event_digest"],
        "reviewer": reviewer,
        "outcome": outcome,
    }


def complete_work_event(event: dict, completion_evidence: dict) -> dict:
    if not completion_evidence.get("condition"):
        raise ValueError("completion requires an explicit condition")
    if not completion_evidence.get("observation"):
        raise ValueError("completion requires supporting observation")

    completed = deepcopy(event)
    completed["completion_state"] = "COMPLETED"
    completed["completion_evidence"] = completion_evidence
    return completed


def amend_work_event(event: dict, review: dict, reason: str, reviewer: str) -> dict:
    if review.get("outcome") != "AMENDMENT_REQUIRED":
        raise ValueError("amendment requires amendment review")
    if not reason or not reviewer:
        raise ValueError("amendment requires reason and reviewer")

    return {
        "record_type": "AMENDMENT",
        "prior_work_event_digest": event["event_digest"],
        "review_digest": digest(review),
        "reason": reason,
        "reviewer": reviewer,
    }


def production_accept(
    reviewed_event: dict,
    verification: dict,
    accepting_authority: str,
) -> dict:
    if reviewed_event.get("review_state") != "REVIEWED":
        raise ValueError("production acceptance requires reviewed state")
    if verification.get("status") != "VERIFIED":
        raise ValueError("production acceptance requires verification")
    if not accepting_authority:
        raise ValueError("production acceptance requires explicit authority")

    return {
        "record_type": "PRODUCTION_ACCEPTANCE",
        "work_event_digest": reviewed_event["event_digest"],
        "verification_digest": digest(verification),
        "accepting_authority": accepting_authority,
        "status": "ACCEPTED",
    }


def run() -> None:
    execution = {
        "status": "EXECUTED",
        "action": "publish",
        "authorization_id": "AUTH-200",
    }

    event = create_work_event(execution)
    original_digest = event["event_digest"]

    # Execution does not imply completion.
    assert event["completion_state"] == "UNKNOWN"

    # Review is a separate record.
    review = review_work_event(event, "ACCEPTED", "HUMAN-REVIEWER")
    reviewed = deepcopy(event)
    reviewed["review_state"] = "REVIEWED"

    # Completion requires an explicit condition and observation.
    completed = complete_work_event(
        reviewed,
        {
            "condition": "published artifact is retrievable",
            "observation": "retrieval check returned artifact",
        },
    )
    assert completed["completion_state"] == "COMPLETED"

    # Production acceptance requires verification and explicit authority.
    verification = {"status": "VERIFIED", "verification_id": "VER-300"}
    production = production_accept(
        completed,
        verification,
        "HUMAN-AUTHORITY",
    )
    assert production["status"] == "ACCEPTED"

    # Amendment never rewrites the original event.
    amendment_review = review_work_event(
        event, "AMENDMENT_REQUIRED", "HUMAN-REVIEWER"
    )
    amendment = amend_work_event(
        event,
        amendment_review,
        "Observed transition was correct but completion interpretation was incomplete.",
        "HUMAN-REVIEWER",
    )
    assert amendment["prior_work_event_digest"] == original_digest
    assert digest(event) == original_digest

    print("PASS: execution does not imply completion")
    print("PASS: review is a separate record")
    print("PASS: completion requires condition and observation")
    print("PASS: production acceptance requires verification and authority")
    print("PASS: amendment preserves immutable WorkEvent history")


if __name__ == "__main__":
    run()
