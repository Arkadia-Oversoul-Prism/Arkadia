"""MVP2-06 — proposal-only orchestration.

This module sequences already-produced Weaver artifacts for operator review.
It deliberately has no execution, commit, push, or authorization capability.
"""
from __future__ import annotations

from typing import Any


AUTONOMY_STATUS = "DISABLED_PROPOSAL_ONLY"


def build_proposal(objective: str, *, plan: dict[str, Any] | None = None,
                    changeset: dict[str, Any] | None = None,
                    patch: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic operator proposal without performing any action."""
    steps: list[dict[str, Any]] = []
    for name, artifact in (("PLAN", plan), ("CHANGESET", changeset), ("PATCH", patch)):
        if artifact is not None:
            steps.append({
                "stage": name,
                "status": "PROPOSED",
                "artifact_present": True,
            })

    return {
        "status": "PROPOSAL_ONLY",
        "objective": objective,
        "autonomy": {
            "status": AUTONOMY_STATUS,
            "enabled": False,
            "authorization_model": "UNDEFINED",
            "reason": "Autonomy remains disabled until an independently defined authorization model exists.",
        },
        "steps": steps,
        "execution": {
            "status": "LOCKED",
            "performed": False,
        },
        "mutation": {
            "performed": False,
            "commit": False,
            "push": False,
        },
        "operator_action_required": True,
    }
