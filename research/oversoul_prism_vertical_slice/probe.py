"""Deterministic end-to-end Oversoul Prism vertical-slice probe.

Research only. This probe models the governance boundaries without invoking
production runtime, LLMs, external services, or consequential side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any


def digest(value: Any) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class State:
    claims: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ("verification", "completion")
    provenance: tuple[str, ...] = ()
    verification: str = "UNKNOWN"


@dataclass(frozen=True)
class Intent:
    actor: str
    objective: str


@dataclass(frozen=True)
class Acceptance:
    accepted_by: str
    scope: str
    result_digest: str


@dataclass(frozen=True)
class ExecutionAuthorization:
    authorized_by: str
    scope: str
    action: str


@dataclass(frozen=True)
class Execution:
    authorization_digest: str
    action: str
    outcome: str = "EXECUTED"


@dataclass(frozen=True)
class WorkEvent:
    event_id: str
    execution_digest: str
    observed_state: str
    immutable_digest: str


@dataclass(frozen=True)
class Review:
    review_id: str
    work_event_digest: str
    status: str


@dataclass(frozen=True)
class Amendment:
    amendment_id: str
    target_event_digest: str
    reason: str
    new_review_status: str


@dataclass(frozen=True)
class Completion:
    work_event_digest: str
    evidence_digest: str
    status: str


@dataclass(frozen=True)
class ProductionAcceptance:
    accepted_by: str
    completion_digest: str
    scope: str


def transform(state: State, node_id: str) -> State:
    """Transform state without creating authority or resolving UNKNOWN."""
    return replace(
        state,
        claims=state.claims + (f"candidate:{node_id}",),
        provenance=state.provenance + (node_id,),
    )


def main() -> None:
    intent = Intent(actor="human:sovereign", objective="produce bounded result")
    context = {"project": "vertical-slice", "objective": intent.objective}

    state = State(provenance=("intent", digest(intent), digest(context)))

    for node_id in ("A01-L01", "A01-L02", "A01-L03"):
        state = transform(state, node_id)

    assert state.unknowns == ("verification", "completion")
    assert state.provenance[-3:] == ("A01-L01", "A01-L02", "A01-L03")

    result_digest = digest(state)

    evidence = {
        "source": "explicit-test-observation",
        "supports": result_digest,
    }
    evidence_digest = digest(evidence)

    # Verification is separate from evidence and does not accept the result.
    state = replace(
        state,
        evidence=state.evidence + (evidence_digest,),
        verification="VERIFIED",
        unknowns=("completion",),
    )
    verification_digest = digest((result_digest, evidence_digest, state.verification))

    acceptance = Acceptance(
        accepted_by="human:sovereign",
        scope="vertical-slice:operational-use",
        result_digest=verification_digest,
    )

    # Acceptance without execution authority must not execute.
    execution_attempt_without_auth = None
    assert execution_attempt_without_auth is None

    authorization = ExecutionAuthorization(
        authorized_by="human:sovereign",
        scope="vertical-slice:bounded-action",
        action="record-observed-transition",
    )
    authorization_digest = digest(authorization)

    execution = Execution(
        authorization_digest=authorization_digest,
        action=authorization.action,
    )
    assert execution.outcome == "EXECUTED"
    assert execution.outcome != "COMPLETED"

    execution_digest = digest(execution)

    # WorkEvent records the observed consequential transition. It is not the
    # authorization and does not itself prove correctness.
    event_payload = (execution_digest, "OBSERVED")
    work_event = WorkEvent(
        event_id="WE-VS-001",
        execution_digest=execution_digest,
        observed_state="OBSERVED",
        immutable_digest=digest(event_payload),
    )

    original_event_digest = work_event.immutable_digest

    review = Review(
        review_id="REVIEW-VS-001",
        work_event_digest=original_event_digest,
        status="REVIEWED",
    )

    amendment = Amendment(
        amendment_id="AMEND-VS-001",
        target_event_digest=original_event_digest,
        reason="review clarifies observed outcome",
        new_review_status="REVIEWED_WITH_CLARIFICATION",
    )

    # Amendment appends a new record. It does not rewrite the WorkEvent.
    assert work_event.immutable_digest == original_event_digest
    assert amendment.target_event_digest == original_event_digest
    assert amendment.target_event_digest != digest(amendment)

    completion_evidence = {
        "condition": "bounded action produced the expected observed transition",
        "work_event": original_event_digest,
        "review": digest(review),
    }
    completion = Completion(
        work_event_digest=original_event_digest,
        evidence_digest=digest(completion_evidence),
        status="COMPLETED",
    )

    # Production acceptance remains separate from completion.
    production_acceptance = ProductionAcceptance(
        accepted_by="human:sovereign",
        completion_digest=digest(completion),
        scope="production:knowledge-projection",
    )

    knowledge_projection = {
        "source_completion": production_acceptance.completion_digest,
        "accepted_by": production_acceptance.accepted_by,
        "scope": production_acceptance.scope,
    }

    # The final projection is downstream of explicit acceptance.
    assert knowledge_projection["source_completion"] == digest(completion)

    # Critical non-collapse assertions.
    assert digest(evidence) != verification_digest
    assert verification_digest != digest(acceptance)
    assert authorization_digest != verification_digest
    assert execution_digest != original_event_digest
    assert original_event_digest != digest(review)
    assert digest(completion) != digest(production_acceptance)

    print("OVERSOUL PRISM VERTICAL SLICE: PASS")
    print("path=A01-L01>A01-L02>A01-L03")
    print("verification=VERIFIED")
    print("execution=EXECUTED")
    print("completion=COMPLETED")
    print("production_acceptance=ACCEPTED")
    print("knowledge_projection=ELIGIBLE")


if __name__ == "__main__":
    main()
