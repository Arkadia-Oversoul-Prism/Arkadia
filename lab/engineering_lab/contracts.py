"""Arkadia Engineering Lab — shared contracts (EL-01 foundational vocabulary).

This module is the single vocabulary source for the native Engineering Lab
substrate. It deliberately *reuses* the frozen vocabularies of the canonical
governance artifacts rather than inventing a parallel one:

  * AEAS-v0.1.1 checkpoint states  (docs/control-plane/AEAS-v0.1.1.md §5)
  * AEAS-v0.1.1 authority levels  (§16)
  * WORKER_CONTRACT-v1 lifecycle  (docs/control-plane/WORKER_CONTRACT.md)
  * SolSpire WorkEvent statuses   (solspire/workevent_manager.py)

Boundary rules encoded here (all normative for the rest of the package):

  PROMPT      != AUTHORIZATION
  SESSION     != AUTHORIZATION
  CAPABILITY  != AUTHORIZATION
  IMPLEMENTED != VERIFIED
  VERIFIED    != MERGED
  MERGED      != DEPLOYED
  PREPARATION != PASSSPEC != K15 != K3

Nothing in this package may create a second identity system, a second
workspace system, a second mutation path, or a second authority path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# -- Boundary doctrine (non-collapse vocabulary) ------------------------------

#: Explicit non-collapses. A state on the left never implies the state on the
#: right without the intervening human act. Exposed so surfaces can render the
#: doctrine truthfully instead of inferring progression.
NON_COLLAPSES: tuple[tuple[str, str], ...] = (
    ("SESSION", "AUTHORIZATION"),
    ("CAPABILITY", "AUTHORIZATION"),
    ("PROMPT", "AUTHORIZATION"),
    ("IMPLEMENTED", "VERIFIED"),
    ("VERIFIED", "MERGED"),
    ("MERGED", "DEPLOYED"),
    ("PREPARATION", "PASSSPEC"),
    ("PASSSPEC", "K15"),
    ("K15", "K3"),
    ("RUNNING", "COMPLETED"),
)

#: Human-only transitions. No agent, session, automation, or surface may cross
#: these; the substrate fails closed at each of them.
HUMAN_ONLY: frozenset[str] = frozenset(
    {"MERGE", "PRODUCTION_DEPLOY", "AUTHORIZE", "SCOPE_EXPANSION", "IDENTITY_BOUNDARY"}
)

#: Operations a bounded agent run may never perform. Mirrors AEAS section 22 and
#: the WORKER_CONTRACT hard prohibitions.
FORBIDDEN_OPERATIONS: frozenset[str] = frozenset(
    {
        "merge",
        "force_push",
        "push_to_main",
        "production_deploy",
        "modify_production_config",
        "modify_credentials",
        "modify_k15_k3",
        "modify_provenance",
        "modify_authority",
        "bypass_authorization",
        "bypass_checkpoint",
        "bypass_test_gate",
    }
)

#: Canonical AEAS authority levels. 0-4 are reachable only inside an
#: architect-authorized bounded task. 5-6 are human-only. 7 is reserved.
#: The Engineering Lab never originates authority; it records and enforces it.
AUTHORITY_LEVELS: dict[int, str] = {
    0: "OBSERVE",
    1: "SUGGEST",
    2: "PREPARE",
    3: "BUILD",
    4: "OPEN_PR",
    5: "MERGE",  # human-only
    6: "DEPLOY",  # human-only
    7: "BOUNDED_AUTONOMY",  # RESERVED / NOT ACTIVE
}

#: The maximum authority the substrate may *represent* without a human act.
LAB_AUTHORITY_CEILING = 2

# -- Canonical checkpoint / session state vocabulary (AEAS section 5) ---------

CHECKPOINT_STATES: tuple[str, ...] = (
    "PROPOSED",
    "AUTHORIZED",
    "QUEUED",
    "RUNNING",
    "CHECKPOINTED",
    "VERIFYING",
    "READY_FOR_REVIEW",
    "REVISION_REQUIRED",
    "BLOCKED",
    "FAILED",
    "COMPLETED",
    "ABORTED",
    "EXPIRED",
)

#: AEAS section 5 semantic non-collapses expressed as forbidden direct
#: transitions. A transition listed here must pass through the intermediate
#: state.
FORBIDDEN_DIRECT_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("AUTHORIZED", "COMPLETED"),
        ("COMPLETED", "AUTHORIZED"),
        ("READY_FOR_REVIEW", "COMPLETED"),
    }
)

#: Legal forward transitions for a governed session, derived from AEAS section 5.
LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROPOSED": frozenset({"AUTHORIZED", "BLOCKED", "ABORTED", "EXPIRED"}),
    "AUTHORIZED": frozenset({"QUEUED", "BLOCKED", "ABORTED", "EXPIRED"}),
    "QUEUED": frozenset({"RUNNING", "BLOCKED", "ABORTED", "EXPIRED"}),
    "RUNNING": frozenset({"CHECKPOINTED", "BLOCKED", "FAILED", "ABORTED"}),
    "CHECKPOINTED": frozenset({"VERIFYING", "BLOCKED", "FAILED", "ABORTED"}),
    "VERIFYING": frozenset(
        {"READY_FOR_REVIEW", "REVISION_REQUIRED", "BLOCKED", "FAILED"}
    ),
    "REVISION_REQUIRED": frozenset({"RUNNING", "BLOCKED", "ABORTED", "EXPIRED"}),
    "READY_FOR_REVIEW": frozenset({"REVISION_REQUIRED", "ABORTED", "EXPIRED"}),
    "BLOCKED": frozenset({"REVISION_REQUIRED", "ABORTED", "EXPIRED"}),
    "FAILED": frozenset({"REVISION_REQUIRED", "ABORTED", "EXPIRED"}),
    # COMPLETED is a human-accepted terminal; the substrate never self-sets it.
    "COMPLETED": frozenset(),
    "ABORTED": frozenset(),
    "EXPIRED": frozenset(),
}

#: States that only a human act may enter. The substrate can *record* them but
#: never *set* them on its own.
HUMAN_TERMINAL_STATES: frozenset[str] = frozenset({"COMPLETED"})

# -- Worker lifecycle (WORKER_CONTRACT-v1) ------------------------------------

WORKER_PHASES: tuple[str, ...] = (
    "WAKE",
    "LOAD",
    "VALIDATE",
    "ROUTE",
    "PLAN",
    "EXECUTE",
    "CHECKPOINT",
    "VERIFY",
    "REPORT",
    "TERMINATE",
)

WORKER_CONTRACT_ID = "ARKADIA-WORKER-CONTRACT-v1"

# -- Evidence vocabulary -------------------------------------------------------

#: Truthful integration states. External services are reported as UNAVAILABLE
#: rather than fabricated.
INTEGRATION_STATES: frozenset[str] = frozenset(
    {"AVAILABLE", "UNAVAILABLE", "UNCONFIGURED", "NOT_ATTEMPTED", "BLOCKED", "UNRESOLVED"}
)

#: Result classification for a bounded task (directive section 19).
RESULT_STATES: frozenset[str] = frozenset(
    {"IMPLEMENTED", "VERIFIED", "BLOCKED", "UNAVAILABLE", "UNRESOLVED", "NOT_ATTEMPTED"}
)


class BoundaryViolation(RuntimeError):
    """Raised when a caller attempts an operation the boundary forbids.

    The substrate fails closed: a forbidden operation raises rather than
    silently degrading or fabricating success.
    """


def assert_operation_allowed(operation: str) -> None:
    """Raise BoundaryViolation if *operation* is forbidden for a bounded run."""
    if operation in FORBIDDEN_OPERATIONS:
        raise BoundaryViolation(
            f"operation '{operation}' is forbidden to bounded agent runs; "
            "it is human-only."
        )


def assert_transition_allowed(current: str, target: str) -> None:
    """Validate a governed session transition against AEAS section 5.

    Raises BoundaryViolation for an unknown state or an illegal transition.
    """
    if current not in LEGAL_TRANSITIONS:
        raise BoundaryViolation(f"unknown current state '{current}'")
    if target not in CHECKPOINT_STATES:
        raise BoundaryViolation(f"unknown target state '{target}'")
    if target not in LEGAL_TRANSITIONS[current]:
        if (current, target) in FORBIDDEN_DIRECT_TRANSITIONS:
            raise BoundaryViolation(
                f"transition {current} -> {target} collapses distinct states; "
                "an intermediate state (e.g. VERIFYING/CHECKPOINTED) is required."
            )
        raise BoundaryViolation(f"illegal transition {current} -> {target}")


@dataclass(frozen=True)
class EvidenceRecord:
    """Durable, attributable evidence for a bounded run.

    Every field is required to be truthful. ``state`` is one of RESULT_STATES;
    no value is inflated (IMPLEMENTED is never reported as VERIFIED).
    """

    evidence_id: str
    subject_ref: str
    workspace_ref: str
    run_ref: str
    state: str
    summary: str
    detail: dict[str, Any]
    timestamp_utc: str
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "subject_ref": self.subject_ref,
            "workspace_ref": self.workspace_ref,
            "run_ref": self.run_ref,
            "state": self.state,
            "summary": self.summary,
            "detail": self.detail,
            "timestamp_utc": self.timestamp_utc,
            "provenance": self.provenance,
        }


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
