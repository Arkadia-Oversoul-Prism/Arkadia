from __future__ import annotations

from typing import Any, Mapping

from lab.evolution.schema import validate_proposal_dict


def build_repair_proposal(
    expected_state: Mapping[str, Any],
    actual_state: Mapping[str, Any],
    *,
    calibration_status: str,
    proposal_id: str = "EV-CAL-001",
) -> dict[str, Any]:
    """Build a Phase 4-shaped repair proposal; never applies or executes it."""
    mismatches = {
        key: {"expected": expected_state.get(key), "actual": actual_state.get(key)}
        for key in sorted(set(expected_state) | set(actual_state))
        if expected_state.get(key) != actual_state.get(key)
    }
    proposal = {
        "proposal_id": proposal_id,
        "title": f"Calibration repair for {calibration_status}",
        "problem": {
            "description": "Observed state differs from the expected state produced by the approved proposal.",
            "evidence": [f"calibration:{key}" for key in mismatches],
        },
        "current_state": dict(actual_state),
        "target_state": dict(expected_state),
        "canon_alignment": "Calibration preserves the existing governed execution and human approval boundary.",
        "affected_components": sorted(mismatches),
        "dependencies": ["Phase 4 proposal schema", "Phase 7 calibration result"],
        "implementation": "Human-reviewed repair only; no automatic application.",
        "tests": ["reproduce calibration mismatch", "verify expected state after human-approved repair"],
        "migration": "None proposed until human approval.",
        "risk": {"technical": "medium", "security": "low", "product": "medium", "rollback": "easy"},
        "expected_outcomes": ["Observed state matches the approved target state."],
        "alternatives": ["Accept the observed deviation as intentional and update the expected state through a new approved proposal."],
        "confidence": 1.0,
        "approval_required": True,
        "execution": False,
        "auto_apply": False,
        "calibration_status": calibration_status,
    }
    errors = validate_proposal_dict(proposal)
    if errors:
        raise ValueError(f"invalid Phase 4 repair proposal: {errors}")
    return proposal
